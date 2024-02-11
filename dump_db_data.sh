if [[ ! -d "dbdump" ]]; then
  mkdir dbdump
fi
pg_dump -h localhost -U postgres -W --data-only chatrooms > "dbdump/chatrooms_$(date '+%Y%m%d_%H%M%S').sql"
