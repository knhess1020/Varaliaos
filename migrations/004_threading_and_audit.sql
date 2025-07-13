-- Enable pgvector if not already
create extension if not exists pgvector;

alter table memory add column if not exists confidence float default 0;
alter table memory add column if not exists merged_into uuid references memory(id);
alter table memory add column if not exists thread_id uuid references conversation_thread(id);
alter table memory add column if not exists turn int;

create table if not exists conversation_thread (
  id uuid primary key default gen_random_uuid(),
  user_id text not null,
  persona text not null,
  started_at timestamptz default now(),
  last_turn int default 0
);

create table if not exists audit_log (
  id bigserial primary key,
  user_id text,
 	action  text,
  mem_id  uuid,
  ts timestamptz default now()
);
