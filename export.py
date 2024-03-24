import asyncio
import sqlite3
import json
import os, sys

import config

P = {'@home':0} # map old pile id to new pile id

def fresh_db():
  if os.path.exists('export.sdb'):
    sys.exit("export.sdb already exists. halting.")
  dbc = sqlite3.connect('export.sdb')
  cur = dbc.cursor()
  cur.executescript("""
    -- everything is an item and has a parent item.
    create table item (
      oi text, -- old id from couchdb (unique but can't drop unique column)
      op text, -- old parent from couchdb
      os text, -- old scene json
      id integer primary key,
      pi integer not null references item(id) default -1,
      ty text not null default '', -- type
      tx text not null, -- text
      ts datetime default current_timestamp);

    create index item_tx on item(tx);

    -- some items have scenes attached. these are 2d graphical
    -- representations that contain a subset of the child items.
    -- think of child items that are not in the scene as a local
    -- "inbox" to be processed.
    create table scene(
      id integer primary key,
      pi integer not null references item(id),
      ci integer not null references item(id),
      x real not null,
      y real not null,
      z integer not null default 0,
      w real not null,
      h real not null,
      c text not null default '',
      unique(pi, ci));

    create view pile as select * from item where ty='pile';

    create view page as
      select p.tx ptx,c.tx ctx,c.ty,s.c,c.pi,c.id ci,s.x,s.y,s.w,s.h
      from (item p left join item c on p.id=c.pi)
        left join scene s on p.id=s.pi and c.id=s.ci
      where p.ty='pile' order by p.tx,s.pi,c.tx""")
  dbc.commit()
  return dbc

def copy_items(dbc, items):
  cur = dbc.cursor()
  for it in items:
    scn=it.get('scene')
    sjs=json.dumps(scn) if scn else None
    cur.execute('insert into item (oi,op,os,ty,tx,ts) values (?,?,?,?,?,?)',
                (it.get('_id'),it.get('pile'),sjs,it.get('type',''),it.get('text',''),it.get('ts')))
  dbc.commit()

def fix_parents(dbc):
  cur = dbc.cursor()
  cur.executescript("""
    update item set tx='@home', id=0 where oi='@home';

    update item set
      pi = case when op is null then -1 -- @home
           else (select id from item i2 where i2.oi = item.op) end; """)
  dbc.commit()

def map_parents(dbc):
  cur = dbc.cursor()
  cur.execute("select oi,id from item")
  for row in cur.fetchall():
    P[row[0]] = row[1]

def map_scenes(dbc):
  cur = dbc.cursor()
  cur.execute("delete from scene")
  cur.execute("select oi,os from item where os is not null")
  for [oi,os] in cur.fetchall():
      scn = json.loads(os)
      for row in scn:
        if not row.get('c'): row['c'] = ''
        row['pi'] = P[oi]
        row['ci'] = P[row['_id']]
        cur.execute("insert into scene (pi,ci,x,y,w,h,c) "
                    "values (:pi,:ci,:x,:y,:w,:h,:c)", row)
  dbc.commit()

def drop_old_columns(dbc):
  cur = dbc.cursor()
  cur.executescript("""
    alter table item drop column oi;
    alter table item drop column op;
    alter table item drop column os;
  """)
  dbc.commit()

async def main():
  fresh_db()
  dbc = sqlite3.connect('export.sdb')
  c = await config.get_client()
  copy_items(dbc, (await c.find(limit=1000, sort=None))['docs'])
  fix_parents(dbc)
  map_parents(dbc)
  map_scenes(dbc)
  drop_old_columns(dbc)
  dbc.close()
  print(80*"-")
  print("created sqlite3 database: export.sdb")
  print("you can ignore the following unclosed connector warnings.")
  print(80*"-")
  # I'd fix them but I'm not using this anymore. :)

if __name__ == '__main__':
  asyncio.run(main())
