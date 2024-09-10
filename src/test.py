def sum_time_with_days(time_list):
    total_seconds = 0
    
    # Convert each time (days:hour:minutes:seconds) into seconds and sum them
    for time_str in time_list:
        d, h, m, s = map(int, time_str.split(':'))
        total_seconds += d * 86400 + h * 3600 + m * 60 + s

    # Convert total seconds back into days, hours, minutes, and seconds
    total_days = total_seconds // 86400
    total_seconds %= 86400
    total_hours = total_seconds // 3600
    total_seconds %= 3600
    total_minutes = total_seconds // 60
    total_seconds %= 60
    
    # Format the result as days:hour:minutes:seconds
    return f"{total_days}:{total_hours:02}:{total_minutes:02}:{total_seconds:02}"

# Example usage:
time_list = ["0:20:23:45", 
             "0:05:12:34", 
             "2:14:34:56",
             ]
total_time = sum_time_with_days(time_list)
print(f"Total time: {total_time}")
