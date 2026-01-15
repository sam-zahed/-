from sqlalchemy import Column, Integer, String, Float, DateTime, JSON, Boolean
from sqlalchemy.sql import func
from .database import Base

class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True, index=True)
    event_id = Column(String, unique=True, index=True)
    user_id = Column(String, index=True)
    timestamp_utc = Column(DateTime)
    trigger_origin = Column(String)
    payload_uri = Column(String)
    features = Column(JSON)
    decision = Column(JSON)
    provenance = Column(JSON)
    storage_policy = Column(String)
    labeled = Column(Boolean, default=False)
    categories = Column(JSON)
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class MapFeature(Base):
    __tablename__ = "map_features"

    id = Column(Integer, primary_key=True, index=True)
    spatial_hash = Column(String, unique=True, index=True)
    feature_class = Column(String)
    location = Column(JSON)  # {lat, lon}
    confidence = Column(Float)
    meta_data = Column(JSON)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class ChangeQueueItem(Base):
    __tablename__ = "change_queue"

    id = Column(Integer, primary_key=True, index=True)
    spatial_hash = Column(String, unique=True, index=True)
    status = Column(String, default="pending")  # pending, accepted, rejected
    occurrences = Column(Integer, default=1)
    accumulated_confidence = Column(Float)
    last_seen = Column(DateTime(timezone=True))
    candidates_data = Column(JSON) # List of raw candidate data
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class LabelingBatch(Base):
    __tablename__ = "labeling_batches"
    
    id = Column(Integer, primary_key=True, index=True)
    batch_id = Column(String, unique=True, index=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    task_count = Column(Integer)
    status = Column(String, default="pending")

class LabelingTask(Base):
    __tablename__ = "labeling_tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_id = Column(String, unique=True, index=True)
    batch_id = Column(String, index=True)
    image_uri = Column(String)
    current_prediction = Column(JSON)
    context = Column(JSON)
    uncertainty_score = Column(Float)
    status = Column(String, default="pending") # pending, completed
    created_at = Column(DateTime(timezone=True), server_default=func.now())
