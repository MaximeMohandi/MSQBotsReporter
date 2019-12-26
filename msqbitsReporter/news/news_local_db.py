from . import exception
import msqbitsReporter.common.constant as constant
import _sqlite3 as db
import feedparser


class LocalDatabase:
    """Connection to the sqlite database"""
    def __init__(self):
        self.conn = db.connect(constant.RESOURCE_FOLDER_PATH + 'msqbreporter_database.db')
        self.__create_news_table()
        self.__NB_ARTICLE_MAX = 4

    def __create_news_table(self):
        """create the tables composing the database"""
        cursor = self.conn.cursor()
        try:
            cursor.executescript('''
                CREATE TABLE IF NOT EXISTS categories (
                    category_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    category_name TEXT NOT NULL
                );
                            
                CREATE TABLE IF NOT EXISTS newspapers (
                    newspaper_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    newspaper_title varchar(255) DEFAULT NULL,
                    newspaper_website varchar(255) DEFAULT NULL,
                    newspaper_rss_link varchar(255) NOT NULL,
                    newspaper_category int(11) NOT NULL,
                    FOREIGN KEY(newspaper_category) REFERENCES categories(category_id)
                );
            ''')

        except Exception:
            raise exception.LocalDatabaseError

        finally:
            cursor.close()

    def insert_newspaper(self, title, website, rss_link, category_name):
        """
        insert a new newspaper into the database

        :param title: newspaper title
        :param website: newspaper website url
        :param rss_link: newspaper rss link
        :param category_name: newspapers category id
        :type title: str
        :type website: str
        :type rss_link: str
        :type category_name: str
        """
        cursor = self.conn.cursor()
        try:
            if self.__is_empty_arg(title, website, rss_link, category_name):
                raise exception.EmptyArgumentError

            cursor.execute('''
                INSERT INTO newspapers (
                    newspaper_title, 
                    newspaper_website, 
                    newspaper_rss_link, 
                    newspaper_category
                ) VALUES (
                    '{}', 
                    '{}', 
                    '{}', 
                    (
                        SELECT c.category_id
                        FROM categories c
                        WHERE c.category_name = '{}'
                    )
                );
            '''.format(title, website, rss_link, category_name))

        except db.DatabaseError:
            raise exception.LocalDatabaseError
        except exception.RssParsingError:
            raise
        finally:
            cursor.close()

    def delete_newspaper(self, newspaper_name):
        """
        Delete the given newspaper

        :param newspaper_name: newspaper name
        :type newspaper_name: str
        """
        cursor = self.conn.cursor()
        try:
            if self.__is_empty_arg(newspaper_name):
                raise exception.EmptyArgumentError

            cursor.execute('''DELETE FROM newspapers WHERE newspaper_title ={}'''.format(newspaper_name))
        except db.DatabaseError:
            raise

        finally:
            cursor.close()

    def select_newspaper(self):
        """
            Get all the newspaper stored into the database

            :returns: list of dictionary with articles from all the newspaper stored in database
            :rtype:list
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT *
                FROM newspapers n
                INNER JOIN categories c ON c.category_id = n.newspaper_category
            ''')

            return self.__format_news(cursor.fetchall())

        except db.DatabaseError:
            raise exception.LocalDatabaseError
        except (exception.NoNewspaperFound, exception.NoArticlesFound):
            raise
        finally:
            cursor.close()

    def select_newspaper_by_title(self, title):
        """
        Get the newspaper with the given name

        :param title: the newspaper name we want to select
        :type title: str

        :return: all newspaper with the given title
        :rtype: list
        """
        cursor = self.conn.cursor()
        try:
            if self.__is_empty_arg(title):
                raise exception.EmptyArgumentError

            cursor.execute('''
                SELECT *
                FROM newspapers n
                INNER JOIN categories c ON c.category_id = n.newspaper_category
                WHERE n.newspaper_title = {}
            '''.format(title))

            return self.__format_news(cursor.fetchall())

        except db.DatabaseError:
            raise exception.LocalDatabaseError
        except (exception.NoNewspaperFound, exception.NoArticlesFound):
            raise
        finally:
            cursor.close()

    def select_newspaper_by_cat(self, category_name):
        """
        Get all the newspaper from the given category

        :param category_name: newspaper category
        :type category_name: str

        :return: all newspaper with into the given category
        :rtype: list
        """
        cursor = self.conn.cursor()
        try:
            if self.__is_empty_arg(category_name):
                raise exception.EmptyArgumentError

            cursor.execute('''
                SELECT *
                FROM newspapers n
                INNER JOIN categories c ON c.category_id = n.newspaper_category
                WHERE c.category_name = {}
            '''.format(category_name))
            return self.__format_news(cursor.fetchall())

        except db.DatabaseError:
            raise exception.LocalDatabaseError
        except (exception.NoNewspaperFound, exception.NoArticlesFound):
            raise
        finally:
            cursor.close()

    def select_categories(self):
        """
        Get all the categories stored into the database

        :return: all category stored
        :rtype: list
        """
        cursor = self.conn.cursor()
        try:
            cursor.execute('''
                SELECT *
                FROM categories
            ''')
            return cursor.fetchall()

        except db.DatabaseError:
            raise exception.LocalDatabaseError
        except (exception.NoNewspaperFound, exception.NoArticlesFound):
            raise
        finally:
            cursor.close()

    def __format_news(self, raw_news):
        """
            format the news fetched from the database to a list of dict

            :param raw_news: list of database row
            :type raw_news: list

            :returns: a list of dict representing the newspaper with the news
            :rtype: list
        """
        try:
            if raw_news is None or len(raw_news) <= 0:
                raise exception.NoNewspaperFound

            for newspaper in raw_news:
                rss_result = feedparser.parse(newspaper[3])
                newspaper_articles = []
                article_count = 0

                if len(newspaper[3]) <= 0:
                    raise exception.NoArticlesFound
                else:
                    while len(rss_result.entries) > 0 and article_count < self.__NB_ARTICLE_MAX:
                        article = rss_result.entries[article_count]
                        newspaper_articles.append({
                            'article_title': article.title,
                            'link': article.link,
                            'date': article.published
                        })
                        article_count += 1

                return {
                    'title': newspaper[1],
                    'description': "//",
                    'website_url': newspaper[2],  # newspaper website
                    'articles': newspaper_articles
                }

        except (feedparser.CharacterEncodingUnknown, feedparser.CharacterEncodingOverride,
                feedparser.NonXMLContentType):
            raise exception.RssParsingError

    def __is_empty_arg(self, *args):
        """
            check if a parameter is empty

            :param args: method argument to check
            :type args: any

            :returns: True if an argument is empty
            :rtype: bool
        """
        for arg in args:
            if arg is None:
                return True
        return False

