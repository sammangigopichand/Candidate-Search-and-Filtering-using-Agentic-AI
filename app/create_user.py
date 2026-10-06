import argparse
import getpass
import sys
from pathlib import Path
from uuid import uuid4


PROJECT_ROOT = Path(__file__).resolve().parent.parent

if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(
        0,
        str(PROJECT_ROOT),
    )


from app.auth_store import (
    auth_database_session,
    create_user,
)


def main():

    parser = argparse.ArgumentParser(
        description="Create recruitment system user."
    )

    parser.add_argument(
        "--username",
        required=True,
    )

    parser.add_argument(
        "--email",
        required=True,
    )

    parser.add_argument(
        "--name",
        required=True,
    )

    parser.add_argument(
        "--role",
        required=True,
        choices=[
            "recruiter",
            "interviewer",
        ],
    )

    parser.add_argument(
        "--id",
        required=False,
    )

    args = parser.parse_args()

    user_id = (
        args.id.strip()
        if args.id
        else str(uuid4())
    )

    print()
    print("Creating user")
    print("-------------")
    print(f"User ID : {user_id}")
    print(f"Username: {args.username}")
    print(f"Email   : {args.email}")
    print(f"Name    : {args.name}")
    print(f"Role    : {args.role}")
    print()

    password = getpass.getpass(
        "Enter password: "
    )

    confirm_password = getpass.getpass(
        "Confirm password: "
    )

    if password != confirm_password:
        print()
        print("Passwords do not match.")
        raise SystemExit(1)

    SessionLocal = auth_database_session()

    db = SessionLocal()

    try:

        user = create_user(
            db,
            user_id=user_id,
            username=args.username,
            email=args.email,
            password=password,
            full_name=args.name,
            role=args.role,
        )

        print()
        print("User created successfully.")
        print()
        print(f"ID       : {user.id}")
        print(f"Username : {user.username}")
        print(f"Name     : {user.full_name}")
        print(f"Email    : {user.email}")
        print(f"Role     : {user.role}")

    except Exception as exc:

        db.rollback()

        print()
        print(f"Failed to create user: {exc}")

        raise SystemExit(1)

    finally:
        db.close()


if __name__ == "__main__":
    main()