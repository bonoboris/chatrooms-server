if [[ ! -d "dbdump" ]]; then
  mkdir dbdump
fi
pg_dump -U postgres -W chatrooms > "dbdump/chatrooms_$(date '+%Y%m%d_%H%M%S').sql"
