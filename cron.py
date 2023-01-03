import schedule
from final import main
import time

# schedule.every(1).day.do(call_cronjob)
# schedule.every().hour.do(job)
schedule.every().day.at("22:31").do(main)
# schedule.every().monday.do(job)
# schedule.every().wednesday.at("13:15").do(job)

while True:
    schedule.run_pending()
    time.sleep(1)