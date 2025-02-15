-- Users table
CREATE TABLE users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active INTEGER DEFAULT 1,
    role TEXT DEFAULT 'user'
);

-- Profiles table
CREATE TABLE profiles (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    preferred_languages TEXT,
    timezone TEXT,
    interests TEXT,
    vision TEXT,
    vibe TEXT,
    goals TEXT,
    user_values TEXT,
    preferences TEXT,
    notification_preferences TEXT,
    privacy_settings TEXT,
    voice_preferences TEXT,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

-- Friendships table
CREATE TABLE friendships (
    user_id INTEGER,
    friend_id INTEGER,
    became_friends_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_interaction TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    interaction_streak INTEGER DEFAULT 0,
    PRIMARY KEY (user_id, friend_id),
    FOREIGN KEY (user_id) REFERENCES users(id),
    FOREIGN KEY (friend_id) REFERENCES users(id)
);

-- Memories table
CREATE TABLE memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    memory_type TEXT,
    visibility TEXT DEFAULT 'mutual',
    is_shared INTEGER DEFAULT 0
);

-- Memory owners association table
CREATE TABLE memory_owners (
    profile_id INTEGER,
    memory_id INTEGER,
    PRIMARY KEY (profile_id, memory_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- Memory shares association table
CREATE TABLE memory_shares (
    profile_id INTEGER,
    memory_id INTEGER,
    PRIMARY KEY (profile_id, memory_id),
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- Media assets table
CREATE TABLE media_assets (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    memory_id INTEGER NOT NULL,
    asset_type TEXT,
    url TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    asset_metadata TEXT,
    original_filename TEXT,
    mime_type TEXT,
    size_bytes INTEGER,
    FOREIGN KEY (memory_id) REFERENCES memories(id)
);

-- AI requests table
CREATE TABLE ai_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER,
    is_anonymous INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    endpoint TEXT,
    prompt_type TEXT,
    response_schema TEXT,
    expected_variables TEXT,
    input_text TEXT,
    input_audio_url TEXT,
    output_text TEXT,
    output_audio_url TEXT,
    duration_ms INTEGER,
    tokens_used INTEGER,
    model_version TEXT,
    status TEXT,
    error TEXT,
    ai_model TEXT,
    temperature REAL,
    top_p REAL,
    top_k INTEGER,
    max_output_tokens INTEGER,
    step_variables TEXT,
    chat_history TEXT,
    FOREIGN KEY (profile_id) REFERENCES profiles(id)
);

-- Tutorial memories table
CREATE TABLE tutorial_memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    profile_id INTEGER NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    step TEXT,
    input_text TEXT,
    response_text TEXT,
    media_asset_id INTEGER,
    ai_request_id INTEGER,
    completed INTEGER DEFAULT 0,
    completion_time TIMESTAMP,
    FOREIGN KEY (profile_id) REFERENCES profiles(id),
    FOREIGN KEY (media_asset_id) REFERENCES media_assets(id),
    FOREIGN KEY (ai_request_id) REFERENCES ai_requests(id)
);

-- Indexes
CREATE INDEX idx_profiles_user_id ON profiles(user_id);
CREATE INDEX idx_media_assets_memory_id ON media_assets(memory_id);
CREATE INDEX idx_ai_requests_profile_id ON ai_requests(profile_id);
CREATE INDEX idx_tutorial_memories_profile_id ON tutorial_memories(profile_id);