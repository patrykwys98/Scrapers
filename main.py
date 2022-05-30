from multiprocessing import Process
import sys
from blogabet import scrap_blogabet
from forum_bukmacherskie import scrap_forum_bukmacherskie
from zt import scrap_zawod_typer

if __name__ == '__main__':
    p1 = Process(target=scrap_blogabet())
    # p2 = Process(target=scrap_forum_bukmacherskie())
    # p3 = Process(target=scrap_zawod_typer())
    p1.start()
    # p2.start()
    # p3.start()
