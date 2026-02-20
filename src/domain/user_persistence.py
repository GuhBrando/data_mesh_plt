from typing import List

from src.infra.postgres import get_db_connection
from src.interface.schemas.user import UserCreate, UserIdentity, UserUpdate


def create_user(user_data: UserCreate) -> UserIdentity:
    """Cria um novo usuário no banco de dados."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            INSERT INTO users (name, email)
            VALUES (%s, %s)
            RETURNING id, name, email;
            """,
            (user_data.name, user_data.email),
        )
        result = cursor.fetchone()
        connection.commit()
        return UserIdentity(id=result[0], name=result[1], email=result[2])


def get_user_by_id(user_id: int) -> UserIdentity | None:
    """Obtém um usuário pelo ID."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, email FROM users WHERE id = %s;", (user_id,))
        result = cursor.fetchone()
        if result:
            return UserIdentity(id=result[0], name=result[1], email=result[2])
        return None


def list_users() -> List[UserIdentity]:
    """Lista todos os usuários."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("SELECT id, name, email FROM users;")
        results = cursor.fetchall()
        return [UserIdentity(id=row[0], name=row[1], email=row[2]) for row in results]


def update_user(user_id: int, user_data: UserUpdate) -> UserIdentity | None:
    """Atualiza os dados de um usuário."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute(
            """
            UPDATE users
            SET name = %s, email = %s
            WHERE id = %s
            RETURNING id, name, email;
            """,
            (user_data.name, user_data.email, user_id),
        )
        result = cursor.fetchone()
        connection.commit()
        if result:
            return UserIdentity(id=result[0], name=result[1], email=result[2])
        return None


def delete_user(user_id: int) -> bool:
    """Exclui um usuário pelo ID."""
    connection = get_db_connection()
    with connection.cursor() as cursor:
        cursor.execute("DELETE FROM users WHERE id = %s;", (user_id,))
        connection.commit()
        return cursor.rowcount > 0
