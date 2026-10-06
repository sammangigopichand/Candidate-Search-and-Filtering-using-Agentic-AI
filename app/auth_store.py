import os
from datetime import datetime, timezone

import bcrypt
from dotenv import load_dotenv

from sqlalchemy import (
    Boolean,
    DateTime,
    String,
    create_engine,
    or_,
    select,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    mapped_column,
    sessionmaker,
)


load_dotenv()


# ============================================================
# DATABASE BASE
# ============================================================

class AuthBase(DeclarativeBase):
    pass


# ============================================================
# USER MODEL
# ============================================================

class User(AuthBase):
    __tablename__ = "users"

    id: Mapped[str] = mapped_column(
        String(36),
        primary_key=True,
    )

    username: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
    )

    email: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    password_hash: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    full_name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    role: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        nullable=False,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


# ============================================================
# DATABASE
# ============================================================

def auth_database_session():
    database_url = os.getenv("DATABASE_URL")

    if not database_url:
        raise RuntimeError(
            "DATABASE_URL is not configured in .env"
        )

    engine = create_engine(
        database_url,
        pool_pre_ping=True,
    )

    AuthBase.metadata.create_all(engine)

    return sessionmaker(
        bind=engine,
        expire_on_commit=False,
    )


# ============================================================
# PASSWORD FUNCTIONS
# ============================================================

def hash_password(password: str) -> str:
    if not password:
        raise ValueError("Password cannot be empty.")

    password_bytes = password.encode("utf-8")

    salt = bcrypt.gensalt()

    hashed = bcrypt.hashpw(
        password_bytes,
        salt,
    )

    return hashed.decode("utf-8")


def verify_password(
    password: str,
    password_hash: str,
) -> bool:

    if not password or not password_hash:
        return False

    try:
        return bcrypt.checkpw(
            password.encode("utf-8"),
            password_hash.encode("utf-8"),
        )
    except (ValueError, TypeError):
        return False


# ============================================================
# VALIDATION
# ============================================================

def validate_role(role: str) -> str:
    role = str(role).strip().lower()

    allowed_roles = {
        "recruiter",
        "interviewer",
    }

    if role not in allowed_roles:
        raise ValueError(
            "Role must be either recruiter or interviewer."
        )

    return role


def validate_password(password: str):
    if len(password) < 8:
        raise ValueError(
            "Password must contain at least 8 characters."
        )


# ============================================================
# CREATE USER
# ============================================================

def create_user(
    db,
    *,
    user_id: str,
    username: str,
    email: str,
    password: str,
    full_name: str,
    role: str,
):

    user_id = str(user_id).strip()
    username = str(username).strip().lower()
    email = str(email).strip().lower()
    full_name = str(full_name).strip()

    role = validate_role(role)

    if not user_id:
        raise ValueError("User ID is required.")

    if not username:
        raise ValueError("Username is required.")

    if not email:
        raise ValueError("Email is required.")

    if not full_name:
        raise ValueError("Full name is required.")

    validate_password(password)

    existing = db.execute(
        select(User).where(
            or_(
                User.id == user_id,
                User.username == username,
                User.email == email,
            )
        )
    ).scalar_one_or_none()

    if existing:
        raise ValueError(
            "User ID, username, or email already exists."
        )

    user = User(
        id=user_id,
        username=username,
        email=email,
        password_hash=hash_password(password),
        full_name=full_name,
        role=role,
        is_active=True,
    )

    db.add(user)
    db.commit()
    db.refresh(user)

    return user


# ============================================================
# AUTHENTICATE
# ============================================================

def authenticate_user(
    db,
    login: str,
    password: str,
):

    login = str(login).strip().lower()

    if not login or not password:
        return None

    user = db.execute(
        select(User).where(
            or_(
                User.username == login,
                User.email == login,
            )
        )
    ).scalar_one_or_none()

    if user is None:
        return None

    if not user.is_active:
        return None

    if not verify_password(
        password,
        user.password_hash,
    ):
        return None

    return user


# ============================================================
# USER QUERIES
# ============================================================

def get_user_by_id(
    db,
    user_id: str,
):

    return db.get(
        User,
        str(user_id).strip(),
    )


def get_user_by_username(
    db,
    username: str,
):

    username = str(username).strip().lower()

    return db.execute(
        select(User).where(
            User.username == username
        )
    ).scalar_one_or_none()


def get_active_interviewers(db):

    return list(
        db.execute(
            select(User)
            .where(
                User.role == "interviewer",
                User.is_active.is_(True),
            )
            .order_by(User.full_name)
        )
        .scalars()
        .all()
    )


def update_interviewer_details(db, user_id: str, *, full_name: str, email: str):
    """Update an interviewer's display name and email address."""
    full_name = str(full_name).strip()
    email = str(email).strip().lower()
    if not full_name:
        raise ValueError("Full name is required.")
    if not email or "@" not in email:
        raise ValueError("Enter a valid email address.")

    user = db.get(User, user_id)
    if user is None or user.role != "interviewer":
        raise ValueError("Interviewer account not found.")

    email_owner = db.execute(
        select(User).where(User.email == email, User.id != user_id)
    ).scalar_one_or_none()
    if email_owner:
        raise ValueError("That email address is already used by another account.")

    user.full_name = full_name
    user.email = email
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db):

    return list(
        db.execute(
            select(User)
            .order_by(
                User.role,
                User.full_name,
            )
        )
        .scalars()
        .all()
    )


# ============================================================
# USER STATUS
# ============================================================

def set_user_active_status(
    db,
    user_id: str,
    is_active: bool,
):

    user = get_user_by_id(
        db,
        user_id,
    )

    if user is None:
        raise ValueError("User not found.")

    user.is_active = bool(is_active)

    db.commit()
    db.refresh(user)

    return user
