from graph import graph

# Commands to initialize indices for Neo4jChatMessageHistory
commands = [
    "CREATE CONSTRAINT IF NOT EXISTS FOR (s:Session) REQUIRE s.id IS UNIQUE",
    "CREATE INDEX IF NOT EXISTS FOR ()-[r:LAST_MESSAGE]-() ON ()",
    "CREATE INDEX IF NOT EXISTS FOR ()-[r:NEXT]-() ON ()",
    "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.content)",
    "CREATE INDEX IF NOT EXISTS FOR (m:Message) ON (m.type)"
]

for cmd in commands:
    print(f"Executing: {cmd}")
    try:
        graph.query(cmd)
    except Exception as e:
        print(f"Error: {e}")

print("Neo4j session history indices initialized (if possible).")
