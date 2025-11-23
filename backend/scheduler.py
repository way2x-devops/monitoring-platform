import time
import schedule
from models.database import SessionLocal, ContainerHistory
import datetime
import cmd
def cleanup_old_data():
    print("🧹 Cleaning up old data...")
    db = SessionLocal()
    
    # Удаляем данные старше 7 дней
    cutoff_date = datetime.datetime.utcnow() - datetime.timedelta(days=7)
    
    deleted_count = db.query(ContainerHistory).filter(
        ContainerHistory.timestamp < cutoff_date
    ).delete()
    
    db.commit()
    print(f"✅ Deleted {deleted_count} old records")

def daily_report():
    print("📊 Generating daily report...")
    # Здесь можно добавить логику отчёта
    pass


# Каждые 5 минут проверяет что все сервисы работают
def health_check():
    # Проверяет доступность API, БД, Redis
    #cmd("sudo docker exec scheduler")
    print('health.check')
    # Отправляет алерт если что-то упало
    pass


def main():
    print("⏰ Scheduler started...")
    
    # Настраиваем расписание
    schedule.every().day.at("02:00").do(cleanup_old_data)  # Каждый день в 2:00
    schedule.every().day.at("09:00").do(daily_report)      # Каждый день в 9:00
    schedule.every(10).minutes.do(health_check)            # Каждые 10 минут
    
    # Бесконечный цикл выполнения задач
    while True:
        schedule.run_pending()
        time.sleep(60)  # Проверяем каждую минуту

if __name__ == "__main__":
    main()