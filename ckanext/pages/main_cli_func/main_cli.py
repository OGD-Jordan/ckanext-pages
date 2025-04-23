from sqlalchemy.exc import SQLAlchemyError
from ckanext.pages.db import MainPage  # Replace with the actual module containing your MainPage class
from ckan import model

def insert_main_page_rows():
    rows = [
        MainPage(
            id=1,
            main_title_1_en = 'Welcome To The Open Government Data Portal In Jordan',
            main_title_1_ar = 'مرحباً بكم في منصة البيانات الحكومية المفتوحة في الأردن',
            main_title_2_en = "Let's start!",
            main_title_2_ar = 'لنبدأ !',
            main_brief_en = 'Find The Data And Resources Needed To Conduct Research, Develop Web And Mobile Applications, And Design Data Visualizations',
            main_brief_ar = 'ابحث عن البيانات والموارد اللازمة لإجراء الأبحاث، وتطوير تطبيقات الويب و الهاتف المحمول، وتصميم تصورات للبيانات',
        ),
        MainPage(
            id=2,
            main_title_1_en = 'Open Data Sectors',
            main_title_1_ar = 'قطاعات البيانات المفتوحة',
            main_brief_en = 'Select The Sector You Are Looking For. Our Data Portal Topics Will Help You Navigate Through Thousands Of Datasets',
            main_brief_ar = 'اختر القطاع الذي تبحث عنه. سيساعدك موضوع بوابة البيانات لدينا على التنقل في آلاف مجموعات البيانات',
        ),
        MainPage(
            id=3,
            main_title_1_en = 'Most Important Indicators',
            main_title_1_ar = 'أهم المؤشرات',
            main_brief_en = '',
            main_brief_ar = '',
        ),
        MainPage(
            id=4,
            main_title_1_en = 'Open Data In Numbers',
            main_title_1_ar = 'البيانات المفتوحة بالأرقام',
            main_brief_en = '',
            main_brief_ar = '',
        ),
        MainPage(
            id=5,
            main_title_1_en = 'Also Explore',
            main_title_1_ar = 'استكشف أيضًا',
            main_brief_en = '',
            main_brief_ar = '',
        ),
    ]

    # Insert the data into the database
    try:
        for row in rows:
            model.Session.add(row)
        model.Session.commit()
        print("Rows inserted successfully!")
    except SQLAlchemyError as e:
        model.Session.rollback()
        print(f"Error inserting rows: {e}")

def delete_all_rows():
    q = MainPage.all()
    for record in q:
        record.delete()
        record.commit()
