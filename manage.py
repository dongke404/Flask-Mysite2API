import app.router
from utils.getNews import GetNews
from app import app
import threading

getNews = GetNews()
t1 = threading.Thread(target=getNews.getsideimg, daemon=True)
t2 = threading.Thread(target=getNews.getbanner, daemon=True)
t3 = threading.Thread(target=getNews.getHotevent, daemon=True)


if __name__ == '__main__':
    t1.start()
    t2.start()
    t3.start()
    app.run()
