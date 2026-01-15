-- schema.sql
CREATE EXTENSION IF NOT EXISTS postgis;
CREATE EXTENSION IF NOT EXISTS pgvector;

CREATE TABLE users (
  user_id UUID PRIMARY KEY,
  consent_profile JSONB,
  locale TEXT,
  preferences JSONB,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE events (
  event_id UUID PRIMARY KEY,
  user_id UUID REFERENCES users(user_id),
  timestamp_utc TIMESTAMP WITH TIME ZONE,
  trigger_origin TEXT,
  payload_uri TEXT,
  features JSONB,
  decision JSONB,
  provenance JSONB,
  storage_policy TEXT,
  labeled BOOLEAN DEFAULT false,
  label_confidence FLOAT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT now()
);

CREATE TABLE labels (
  label_id UUID PRIMARY KEY,
  event_id UUID REFERENCES events(event_id),
  label_type TEXT,
  label_value TEXT,
  labeled_by TEXT,
  timestamp TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE change_queue (
  id UUID PRIMARY KEY,
  user_id UUID,
  region_geo GEOMETRY,
  hypothesis JSONB,
  occurrence_count INT DEFAULT 1,
  accumulated_confidence FLOAT DEFAULT 0.0,
  last_seen TIMESTAMPTZ,
  status TEXT
);
