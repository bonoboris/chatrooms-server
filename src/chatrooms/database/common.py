"""Database helpers functions."""

from collections import abc
from collections.abc import Iterable
from typing import Any, Literal, LiteralString, NamedTuple, TypeGuard, TypeVar

from psycopg import sql
from psycopg.cursor_async import AsyncCursor
from psycopg.rows import Row

TLiteralStr = TypeVar("TLiteralStr", bound=LiteralString)


class InvalidColumnError(ValueError):
    """Invalid column name."""

    def __init__(self, column: str, columns: abc.Sequence[str] | None = None) -> None:
        super().__init__(f"Invalid column name: '{column}', expected one of: {columns}")


def check_cols(
    to_check: abc.Sequence[str], columns: tuple[TLiteralStr, ...]
) -> TypeGuard[abc.Sequence[TLiteralStr]]:
    """Check if all `to_check` values are in `columns`."""
    for col in to_check:
        if col not in columns:
            raise InvalidColumnError(col, columns)
    return True


def order_by(
    columns: tuple[LiteralString, ...],
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
) -> sql.Composed | sql.SQL:
    """Return ORDER BY clause."""
    if sort_by is None:
        return sql.SQL("")
    if sort_by not in columns:
        raise InvalidColumnError(sort_by, columns)
    return sql.SQL("ORDER BY {sort_by} {sort_dir}").format(
        sort_by=sql.Identifier(sort_by), sort_dir=sql.SQL(sort_dir)
    )


def placeholder_values(
    values: Iterable[str], sep: LiteralString = ", "
) -> sql.Composable | sql.SQL:
    """Return joined placeholder values.

    Example:
        ```python
        >>> placeholder_values(["a", "b", "c"]).as_string()
        'a = $(a)s, b = $(b)s, c = $(c)s'
        >>> placeholder_values(["a", "b", "c"], sep=" AND ").as_string()
        'a = $(a)s AND b = $(b)s AND c = $(c)s'
        ```
    """
    if not values:
        return sql.SQL("")
    return sql.SQL(sep).join(
        sql.SQL("{indentifier} = {placeholder}").format(
            indentifier=sql.Identifier(value), placeholder=sql.Placeholder(value)
        )
        for value in values
    )


def c_where(
    columns: tuple[LiteralString, ...],
    wheres: abc.Sequence[str] = (),
) -> sql.Composed | sql.SQL:
    """Return WHERE clause."""
    if not wheres:
        return sql.SQL("")
    assert check_cols(wheres, columns)
    return sql.SQL("WHERE ") + sql.SQL(" AND ").join(
        sql.SQL("{indentifier} = {placeholder}").format(
            indentifier=sql.Identifier(where), placeholder=sql.Placeholder(where)
        )
        for where in wheres
    )


def q_select(
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    wheres: abc.Sequence[str] = (),
    *,
    limit: bool = True,
) -> sql.Composed | sql.SQL:
    """Return SELECT * query with WHERE, SORT_BY, and/or LIMIT clauses.

    Query will expect named values 'limit', 'skip' if `limit` param is True and all `wheres`.

    Raise if any of `wheres` or `sort_by` is not in `columns`
    """
    return sql.SQL(
        """\
            SELECT *
            FROM {table}
            {where}
            {order_by}
            {limit}
            """
    ).format(
        table=sql.Identifier(table),
        where=c_where(columns, wheres),
        order_by=order_by(columns, sort_by, sort_dir),
        limit=sql.SQL("LIMIT %(limit)s OFFSET %(skip)s" if limit else ""),
    )


async def select(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    sort_by: str | None = None,
    sort_dir: Literal["asc", "desc"] = "asc",
    limit: int | None = None,
    skip: int | None = None,
    **wheres: Any,
) -> AsyncCursor[Row]:
    """Execute a SELECT * query with WHERE, SORT_BY, and/or LIMIT clauses.

    Raise if any of `wheres` or `sort_by` is not in `columns`
    """
    return await cursor.execute(
        q_select(
            table,
            columns=columns,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit is not None,
            wheres=list(wheres),
        ),
        {"limit": limit, "skip": 0 if skip is None and limit is not None else skip, **wheres},
    )


def q_insert(
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    values: abc.Sequence[str],
) -> sql.Composed | sql.SQL:
    """Return INSERT INTO query with given column values.

    Raise if any of `values` key is not in `columns`
    """
    assert check_cols(values, columns)
    return sql.SQL(
        """
            INSERT INTO {table}({columns})
            VALUES ({values})
            RETURNING *
            """
    ).format(
        table=sql.Identifier(table),
        columns=sql.SQL(", ").join(map(sql.Identifier, values)),
        values=sql.SQL(", ").join(map(sql.Placeholder, values)),
    )


async def insert(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    **values: Any,
) -> AsyncCursor[Row]:
    """Return INSERT INTO query with given column values.

    Raise if any of `values` key is not in `columns`
    """
    return await cursor.execute(q_insert(table, columns=columns, values=list(values)), values)


def q_update(
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    wheres: abc.Sequence[str],
    sets: abc.Sequence[str],
) -> sql.Composed | sql.SQL:
    """Return UPDATE query with given column values, with WHERE clause.

    Raise if any of `values` or `wheres` key is not in `columns`
    """
    assert check_cols(sets, columns)
    return sql.SQL(
        """
            UPDATE {table}
            SET {values}
            {wheres}
            RETURNING *
            """
    ).format(
        table=sql.Identifier(table),
        values=sql.SQL(", ").join(
            sql.SQL("{indentifier} = {placeholder}").format(
                indentifier=sql.Identifier(value), placeholder=sql.Placeholder(value)
            )
            for value in sets
        ),
        wheres=c_where(columns, wheres),
    )


async def update_by_id(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    id: int,
    **values: Any,
) -> AsyncCursor[Row]:
    """Execute an UPDATE query with WHERE clause on id.

    Raise if any of `values` is not in `columns`
    """
    return await cursor.execute(
        q_update(table, columns=columns, wheres=["id"], sets=list(values)), {**values, "id": id}
    )


async def update(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    wheres: dict[str, Any],
    values: dict[str, Any],
) -> AsyncCursor[Row]:
    """Execute an UPDATE query with WHERE clause.

    Raise if any of `values` or `wheres` is not in `columns`
    """
    return await cursor.execute(
        q_update(table, columns=columns, wheres=list(wheres), sets=list(values)),
        {**values, **wheres},
    )


def q_delete(
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    wheres: abc.Sequence[str],
) -> sql.Composed | sql.SQL:
    """Return DELETE FROM query with WHERE clause.

    Raise if any of `wheres` key is not in `columns`
    """
    return sql.SQL(
        """
            DELETE FROM {table}
            {wheres}
            """
    ).format(table=sql.Identifier(table), wheres=c_where(columns, wheres))


async def delete_by_id(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    id: int,
) -> AsyncCursor[Row]:
    """Execute an DELETE FROM query with WHERE clause on id."""
    return await cursor.execute(q_delete(table, columns=columns, wheres=["id"]), {"id": id})


async def delete(
    cursor: AsyncCursor[Row],
    table: LiteralString,
    columns: tuple[LiteralString, ...],
    wheres: dict[str, Any],
) -> AsyncCursor[Row]:
    """Execute an DELETE FROM query with WHERE clause.

    Raise if any of `wheres` is not in `columns`
    """
    return await cursor.execute(
        q_delete(table, columns=columns, wheres=list(wheres)),
        wheres,
    )


class Querier(NamedTuple):
    """Query builder / executer."""

    table: LiteralString
    columns: tuple[LiteralString, ...]

    def q_select(
        self,
        sort_by: str | None = None,
        sort_dir: Literal["asc", "desc"] = "asc",
        wheres: abc.Sequence[str] = (),
        *,
        limit: bool = True,
    ) -> sql.Composed | sql.SQL:
        """Return SELECT * query with WHERE, SORT_BY, and/or LIMIT clauses.

        Query will expect named values 'limit', 'skip' if `limit` param is True and all `wheres`.

        Raise if any of `wheres` or `sort_by` is not in `columns`
        """
        return q_select(
            table=self.table,
            columns=self.columns,
            sort_by=sort_by,
            sort_dir=sort_dir,
            wheres=wheres,
            limit=limit,
        )

    async def select(
        self,
        cursor: AsyncCursor[Row],
        sort_by: str | None = None,
        sort_dir: Literal["asc", "desc"] = "asc",
        limit: int | None = None,
        skip: int | None = None,
        **wheres: Any,
    ) -> AsyncCursor[Row]:
        """Execute a SELECT * query with WHERE, SORT_BY, and/or LIMIT clauses.

        Raise if any of `wheres` or `sort_by` is not in `columns`
        """
        return await select(
            cursor=cursor,
            table=self.table,
            columns=self.columns,
            sort_by=sort_by,
            sort_dir=sort_dir,
            limit=limit,
            skip=skip,
            **wheres,
        )

    def q_insert(self, values: abc.Sequence[str]) -> sql.Composed | sql.SQL:
        """Return INSERT INTO query with given column values.

        Raise if any of `values` key is not in `columns`
        """
        return q_insert(table=self.table, columns=self.columns, values=values)

    async def insert(self, cursor: AsyncCursor[Row], **values: Any) -> AsyncCursor[Row]:
        """Return INSERT INTO query with given column values.

        Raise if any of `values` key is not in `columns`
        """
        return await insert(cursor=cursor, table=self.table, columns=self.columns, **values)

    def q_update(
        self, wheres: abc.Sequence[str], sets: abc.Sequence[str]
    ) -> sql.Composed | sql.SQL:
        """Return UPDATE query with given column values, with WHERE clause.

        Raise if any of `values` or `wheres` key is not in `columns`
        """
        return q_update(table=self.table, columns=self.columns, wheres=wheres, sets=sets)

    async def update_by_id(
        self, cursor: AsyncCursor[Row], id: int, **values: Any
    ) -> AsyncCursor[Row]:
        """Execute an UPDATE query with WHERE clause on id.

        Raise if any of `values` is not in `columns`
        """
        return await update_by_id(
            cursor=cursor, table=self.table, columns=self.columns, id=id, **values
        )

    async def update(
        self, cursor: AsyncCursor[Row], wheres: dict[str, Any], values: dict[str, Any]
    ) -> AsyncCursor[Row]:
        """Execute an UPDATE query with WHERE clause.

        Raise if any of `values` or `wheres` is not in `columns`
        """
        return await update(
            cursor=cursor, table=self.table, columns=self.columns, wheres=wheres, values=values
        )

    def q_delete(
        self,
        wheres: abc.Sequence[str],
    ) -> sql.Composed | sql.SQL:
        """Return DELETE FROM query with WHERE clause.

        Raise if any of `wheres` key is not in `columns`
        """
        return q_delete(table=self.table, columns=self.columns, wheres=wheres)

    async def delete_by_id(self, cursor: AsyncCursor[Row], id: int) -> AsyncCursor[Row]:
        """Execute an DELETE FROM query with WHERE clause on id."""
        return await delete_by_id(cursor=cursor, table=self.table, columns=self.columns, id=id)

    async def delete(self, cursor: AsyncCursor[Row], wheres: dict[str, Any]) -> AsyncCursor[Row]:
        """Execute an DELETE FROM query with WHERE clause.

        Raise if any of `wheres` is not in `columns`
        """
        return await delete(cursor=cursor, table=self.table, columns=self.columns, wheres=wheres)
