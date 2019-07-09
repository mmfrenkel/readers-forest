import requests
import os


class GoodreadsAPI:

    def __init__(self):
        self.base_url = "https://www.goodreads.com"
        self.api_key = self._get_api_key()
        self.format = "json"

    def get_average_rating(self, isbn):
        """Returns the average rating of the edition of the book (isbn)."""

        review = self._get_review_by_isbn(isbn)
        return review['average_rating']

    def get_number_ratings(self, isbn):
        """Returns the total number of ratings cast for a particular edition
        of the book (isbn)."""

        review = self._get_review_by_isbn(isbn)
        return review['ratings_count']

    @staticmethod
    def _get_api_key():
        """Fetches the api key from environmental variables."""

        if not os.getenv("GOODREADS_API_KEY"):
            raise RuntimeError("GOODREADS_API_KEY is not set")

        return os.getenv("GOODREADS_API_KEY")

    def _get_review_by_isbn(self, isbn):
        """
        Fetches the review information from the Goodreads API
        :param isbn: The known, single isbn number for a book edition
        :return: json object, containing response details for that book
        """

        url = self.base_url + "/book/review_counts." + self.format
        res = requests.get(url, params={"key": self.api_key, "isbns": isbn})

        if res.status_code != 200:
            raise Exception("Uh oh. Goodreads API request was unsuccessful!")

        return res.json()['books'][0]



