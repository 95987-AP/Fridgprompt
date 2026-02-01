"""SQLite storage for Fridgprompt."""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from .models import Prompt, TRAITS


def get_db_path() -> Path:
    """Get the database path, creating directories if needed."""
    # Store in user's home directory
    db_dir = Path.home() / ".fridgprompt"
    db_dir.mkdir(exist_ok=True)
    return db_dir / "prompts.db"


def get_connection() -> sqlite3.Connection:
    """Get a database connection."""
    conn = sqlite3.connect(get_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Initialize the database schema."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS prompts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content TEXT NOT NULL,
            outcome TEXT,
            rating INTEGER CHECK(rating >= 1 AND rating <= 5),
            model TEXT,
            task_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS tags (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        );

        CREATE TABLE IF NOT EXISTS prompt_tags (
            prompt_id INTEGER REFERENCES prompts(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (prompt_id, tag_id)
        );

        CREATE TABLE IF NOT EXISTS traits (
            prompt_id INTEGER REFERENCES prompts(id) ON DELETE CASCADE,
            trait_name TEXT NOT NULL,
            detected BOOLEAN NOT NULL,
            PRIMARY KEY (prompt_id, trait_name)
        );

        CREATE INDEX IF NOT EXISTS idx_prompts_rating ON prompts(rating);
        CREATE INDEX IF NOT EXISTS idx_prompts_created ON prompts(created_at);
        CREATE INDEX IF NOT EXISTS idx_tags_name ON tags(name);

        -- Full-text search
        CREATE VIRTUAL TABLE IF NOT EXISTS prompts_fts USING fts5(
            content,
            outcome,
            content='prompts',
            content_rowid='id'
        );

        -- Triggers to keep FTS in sync
        CREATE TRIGGER IF NOT EXISTS prompts_ai AFTER INSERT ON prompts BEGIN
            INSERT INTO prompts_fts(rowid, content, outcome)
            VALUES (new.id, new.content, new.outcome);
        END;

        CREATE TRIGGER IF NOT EXISTS prompts_ad AFTER DELETE ON prompts BEGIN
            INSERT INTO prompts_fts(prompts_fts, rowid, content, outcome)
            VALUES('delete', old.id, old.content, old.outcome);
        END;

        CREATE TRIGGER IF NOT EXISTS prompts_au AFTER UPDATE ON prompts BEGIN
            INSERT INTO prompts_fts(prompts_fts, rowid, content, outcome)
            VALUES('delete', old.id, old.content, old.outcome);
            INSERT INTO prompts_fts(rowid, content, outcome)
            VALUES (new.id, new.content, new.outcome);
        END;
    """)

    conn.commit()
    conn.close()


def add_prompt(prompt: Prompt) -> int:
    """Add a new prompt and return its ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO prompts (content, outcome, rating, model, task_type, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        prompt.content,
        prompt.outcome,
        prompt.rating,
        prompt.model,
        prompt.task_type,
        prompt.created_at,
        prompt.updated_at,
    ))

    prompt_id = cursor.lastrowid

    # Add tags
    for tag_name in prompt.tags:
        cursor.execute("INSERT OR IGNORE INTO tags (name) VALUES (?)", (tag_name,))
        cursor.execute("SELECT id FROM tags WHERE name = ?", (tag_name,))
        tag_id = cursor.fetchone()["id"]
        cursor.execute(
            "INSERT OR IGNORE INTO prompt_tags (prompt_id, tag_id) VALUES (?, ?)",
            (prompt_id, tag_id)
        )

    conn.commit()
    conn.close()

    return prompt_id


def get_prompt(prompt_id: int) -> Optional[Prompt]:
    """Get a prompt by ID."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM prompts WHERE id = ?", (prompt_id,))
    row = cursor.fetchone()

    if not row:
        conn.close()
        return None

    # Get tags
    cursor.execute("""
        SELECT t.name FROM tags t
        JOIN prompt_tags pt ON t.id = pt.tag_id
        WHERE pt.prompt_id = ?
    """, (prompt_id,))
    tags = [r["name"] for r in cursor.fetchall()]

    # Get traits
    cursor.execute(
        "SELECT trait_name, detected FROM traits WHERE prompt_id = ?",
        (prompt_id,)
    )
    traits = {r["trait_name"]: bool(r["detected"]) for r in cursor.fetchall()}

    conn.close()

    return Prompt(
        id=row["id"],
        content=row["content"],
        outcome=row["outcome"],
        rating=row["rating"],
        model=row["model"],
        task_type=row["task_type"],
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        tags=tags,
        traits=traits,
    )


def list_prompts(
    tag: Optional[str] = None,
    rating: Optional[int] = None,
    limit: int = 20,
    offset: int = 0,
) -> list[Prompt]:
    """List prompts with optional filters."""
    conn = get_connection()
    cursor = conn.cursor()

    query = "SELECT DISTINCT p.* FROM prompts p"
    params = []

    if tag:
        query += """
            JOIN prompt_tags pt ON p.id = pt.prompt_id
            JOIN tags t ON pt.tag_id = t.id
            WHERE t.name = ?
        """
        params.append(tag)
        if rating is not None:
            query += " AND p.rating = ?"
            params.append(rating)
    elif rating is not None:
        query += " WHERE p.rating = ?"
        params.append(rating)

    query += " ORDER BY p.created_at DESC LIMIT ? OFFSET ?"
    params.extend([limit, offset])

    cursor.execute(query, params)
    rows = cursor.fetchall()

    prompts = []
    for row in rows:
        # Get tags for each prompt
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN prompt_tags pt ON t.id = pt.tag_id
            WHERE pt.prompt_id = ?
        """, (row["id"],))
        tags = [r["name"] for r in cursor.fetchall()]

        prompts.append(Prompt(
            id=row["id"],
            content=row["content"],
            outcome=row["outcome"],
            rating=row["rating"],
            model=row["model"],
            task_type=row["task_type"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=tags,
        ))

    conn.close()
    return prompts


def search_prompts(query: str, limit: int = 20) -> list[Prompt]:
    """Full-text search prompts."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.* FROM prompts p
        JOIN prompts_fts fts ON p.id = fts.rowid
        WHERE prompts_fts MATCH ?
        ORDER BY rank
        LIMIT ?
    """, (query, limit))

    rows = cursor.fetchall()

    prompts = []
    for row in rows:
        cursor.execute("""
            SELECT t.name FROM tags t
            JOIN prompt_tags pt ON t.id = pt.tag_id
            WHERE pt.prompt_id = ?
        """, (row["id"],))
        tags = [r["name"] for r in cursor.fetchall()]

        prompts.append(Prompt(
            id=row["id"],
            content=row["content"],
            outcome=row["outcome"],
            rating=row["rating"],
            model=row["model"],
            task_type=row["task_type"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            tags=tags,
        ))

    conn.close()
    return prompts


def rate_prompt(prompt_id: int, rating: int, outcome: Optional[str] = None) -> bool:
    """Rate a prompt and optionally add outcome notes."""
    conn = get_connection()
    cursor = conn.cursor()

    if outcome:
        cursor.execute("""
            UPDATE prompts
            SET rating = ?, outcome = ?, updated_at = ?
            WHERE id = ?
        """, (rating, outcome, datetime.now(), prompt_id))
    else:
        cursor.execute("""
            UPDATE prompts
            SET rating = ?, updated_at = ?
            WHERE id = ?
        """, (rating, datetime.now(), prompt_id))

    affected = cursor.rowcount
    conn.commit()
    conn.close()

    return affected > 0


def save_traits(prompt_id: int, traits: dict[str, bool]) -> None:
    """Save detected traits for a prompt."""
    conn = get_connection()
    cursor = conn.cursor()

    for trait_name, detected in traits.items():
        cursor.execute("""
            INSERT OR REPLACE INTO traits (prompt_id, trait_name, detected)
            VALUES (?, ?, ?)
        """, (prompt_id, trait_name, detected))

    conn.commit()
    conn.close()


def get_prompts_for_analysis() -> list[Prompt]:
    """Get prompts that haven't been analyzed for traits yet."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT p.* FROM prompts p
        WHERE p.id NOT IN (SELECT DISTINCT prompt_id FROM traits)
    """)

    rows = cursor.fetchall()
    prompts = [
        Prompt(
            id=row["id"],
            content=row["content"],
            outcome=row["outcome"],
            rating=row["rating"],
            model=row["model"],
            task_type=row["task_type"],
        )
        for row in rows
    ]

    conn.close()
    return prompts


def get_trait_stats() -> dict:
    """Get trait statistics for insights."""
    conn = get_connection()
    cursor = conn.cursor()

    # Get trait frequency for high-rated prompts (4-5)
    cursor.execute("""
        SELECT t.trait_name,
               COUNT(*) as total,
               SUM(CASE WHEN t.detected THEN 1 ELSE 0 END) as detected_count
        FROM traits t
        JOIN prompts p ON t.prompt_id = p.id
        WHERE p.rating >= 4
        GROUP BY t.trait_name
    """)
    high_rated = {
        row["trait_name"]: row["detected_count"] / row["total"] * 100 if row["total"] > 0 else 0
        for row in cursor.fetchall()
    }

    # Get trait frequency for low-rated prompts (1-2)
    cursor.execute("""
        SELECT t.trait_name,
               COUNT(*) as total,
               SUM(CASE WHEN t.detected THEN 1 ELSE 0 END) as detected_count
        FROM traits t
        JOIN prompts p ON t.prompt_id = p.id
        WHERE p.rating <= 2
        GROUP BY t.trait_name
    """)
    low_rated = {
        row["trait_name"]: row["detected_count"] / row["total"] * 100 if row["total"] > 0 else 0
        for row in cursor.fetchall()
    }

    # Get overall stats
    cursor.execute("SELECT COUNT(*) as total FROM prompts")
    total = cursor.fetchone()["total"]

    cursor.execute("SELECT COUNT(*) as rated FROM prompts WHERE rating IS NOT NULL")
    rated = cursor.fetchone()["rated"]

    cursor.execute("SELECT AVG(rating) as avg FROM prompts WHERE rating IS NOT NULL")
    avg_row = cursor.fetchone()
    avg_rating = avg_row["avg"] if avg_row["avg"] else 0

    conn.close()

    return {
        "total_prompts": total,
        "rated_prompts": rated,
        "avg_rating": avg_rating,
        "high_rated_traits": high_rated,
        "low_rated_traits": low_rated,
    }


def get_all_tags() -> list[str]:
    """Get all unique tags."""
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM tags ORDER BY name")
    tags = [row["name"] for row in cursor.fetchall()]
    conn.close()
    return tags
