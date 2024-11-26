if [[ ! -d "dbdump" ]]; then
  mkdir dbdump
fi
pg_dump -U postgres -W --data-only chatrooms > "dbdump/data_chatrooms_$(date '+%Y%m%d_%H%M%S').sql"
