import random
from scrapy import signals
from scrapy.downloadermiddlewares.retry import RetryMiddleware
from scrapy.exceptions import IgnoreRequest
from scrapy.utils.response import response_status_message


class RedirectRetryMiddleware(RetryMiddleware):
    """
    A custom RetryMiddleware to handle redirects and retry logic.
    Will retry the request on a 301 or 302 redirect, with improved logging and flexibility.
    """

    def handle_redirect_response(self, request, response, spider):
        """
        Process the response for redirects (301/302) and retry the request if necessary.
        Enhanced with custom retry logic and logging.
        """
        if response.status in [301, 302]:
            redirect_url = response.headers.get('Location', '').decode()
            spider.logger.warning(f"Redirect detected for {request.url} to {redirect_url}")

            # Custom retry count handling
            retry_count = request.meta.get("retry_count", 0)
            max_retries = self.max_retry_times

            # Retry conditions based on the response's 'Location' header
            if retry_count >= max_retries:
                spider.logger.error(f"Max retries reached for {request.url}. Giving up after redirect to {redirect_url}.")
                return response

            # Log different retry attempts based on status code
            spider.logger.info(f"Retrying {request.url} ({retry_count + 1}/{max_retries}) due to redirect to {redirect_url}")
            retry_count += 1

            # Retry with modified request
            new_request = request.copy()
            new_request.meta["retry_count"] = retry_count
            return self._retry(new_request, response_status_message(response.status), spider) or response

        return response



class TotalCountRetryMiddleware:
    """
    A middleware to handle retry attempts based on missing 'total_count' data.
    If 'total_count' is missing from a response, it will retry the request until the max retries are reached.
    """

    def __init__(self, retry_attempts, force_retry_urls=None):
        self.retry_attempts = retry_attempts
        self.force_retry_urls = force_retry_urls or []

    @classmethod
    def from_crawler(cls, crawler):
        retry_attempts = crawler.settings.getint("RETRY_TIMES", 10)
        force_retry_urls = crawler.settings.getlist("FORCE_RETRY_URLS", [])
        return cls(retry_attempts, force_retry_urls)

    def handle_missing_total_count(self, request, response, spider):
        """
        Handle retry logic if 'total_count' is missing from the response.
        Enhanced with custom URL retry logic.
        """
        if "captcha" in response.url:
            spider.logger.warning(f"Captcha detected on {request.url}, skipping retries")
            raise IgnoreRequest(f"Captcha detected for {request.url}")

        total_count_str = response.xpath('//span[@class="content__title--hl"]/text()').get()
        if total_count_str:
            return response

        retry_attempts = request.meta.get("retry_attempts", 0)
        
        # Check if we are forced to retry specific URLs, even if the total_count is missing
        if request.url in self.force_retry_urls:
            spider.logger.info(f"Forcing retry for {request.url}, total_count missing (attempt {retry_attempts + 1})")
            return self._retry_request(request, retry_attempts, spider)

        # Regular retry logic for missing total_count
        if retry_attempts < self.retry_attempts:
            spider.logger.info(f"Retrying {request.url} due to missing total_count (attempt {retry_attempts + 1})")
            return self._retry_request(request, retry_attempts, spider)
        else:
            spider.logger.warning(f"Giving up on {request.url} after {retry_attempts} retries due to missing total_count")
            raise IgnoreRequest(f"Missing total_count_str after {retry_attempts} retries")

    def _retry_request(self, request, retry_attempts, spider):
        """
        Internal method to handle the retry request logic.
        """
        retry_req = request.copy()
        retry_req.meta["retry_attempts"] = retry_attempts + 1
        retry_req.dont_filter = True
        return retry_req


class LianjiaSpiderMiddleware:
    """
    The spider middleware is responsible for handling and processing responses.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def process_spider_input(self, response, spider):
        return None

    def process_spider_output(self, response, result, spider):
        yield from result

    def process_spider_exception(self, response, exception, spider):
        pass

    def process_start_requests(self, start_requests, spider):
        yield from start_requests

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")


class LianjiaDownloaderMiddleware:
    """
    Middleware to handle requests and responses during the downloading phase.
    """

    @classmethod
    def from_crawler(cls, crawler):
        s = cls()
        crawler.signals.connect(s.spider_opened, signal=signals.spider_opened)
        return s

    def handle_request(self, request, spider):
        return None

    def handle_response(self, request, response, spider):
        return response

    def handle_exception(self, request, exception, spider):
        pass

    def spider_opened(self, spider):
        spider.logger.info(f"Spider opened: {spider.name}")


class ProxyMiddleware:
    """
    A custom middleware to add proxy support for requests.
    Randomly selects a proxy from a pre-defined list or chooses based on custom logic.
    """

    def __init__(self, proxy_list=None, proxy_selector=None):
        self.proxy_list = proxy_list or [
            "http://t13410580638224:ib4h6iwz@w935.kdltps.com:？？？？？",  # 填入自己的 proxy
        ]
        self.proxy_selector = proxy_selector or self.random_proxy

    def handle_request_with_proxy(self, request, spider):
        """
        Selects a proxy using the specified logic and attaches it to the request.
        """
        proxy = self.proxy_selector(request, spider)
        request.meta["proxy"] = proxy
        spider.logger.info(f"Using Proxy: {proxy}")

    def random_proxy(self, request, spider):
        """
        Default proxy selector that randomly selects a proxy from the list.
        """
        return random.choice(self.proxy_list)

    def custom_proxy_selector(self, request, spider):
        """
        A custom proxy selector method that could choose proxies based on request URL,
        headers, or other dynamic factors.
        """
        if "example.com" in request.url:
            return "http://example_proxy:port"
        return random.choice(self.proxy_list)



class CloseConnectionMiddleware:
    """
    A middleware that conditionally modifies the 'Connection' header to 'close'.
    It will only apply this header modification based on certain conditions,
    such as a specific URL pattern or other request meta data.
    """

    def modify_connection_header(self, request, spider):
        """
        Conditionally set the 'Connection' header to 'close' based on request characteristics.
        Adds additional logging for debugging purposes.
        """
        # Check if the request URL matches a specific pattern
        if "some_condition" in request.url:
            request.headers["Connection"] = "close"
            spider.logger.info(f"Connection header set to 'close' for URL: {request.url}")

        # Another example: If the request is marked with a specific meta attribute
        elif request.meta.get("force_close", False):
            request.headers["Connection"] = "close"
            spider.logger.info(f"Connection header forcibly set to 'close' for URL: {request.url}")

        # Optionally, you could add a fallback mechanism for certain conditions
        elif self.should_modify_connection(request):
            request.headers["Connection"] = "close"
            spider.logger.info(f"Connection header set to 'close' by fallback logic for URL: {request.url}")

    def should_modify_connection(self, request):
        """
        A custom logic to determine if the 'Connection' header should be modified.
        This can be based on specific request conditions or URL patterns.
        """
        # Example: Modify connection header for all requests going to a specific domain
        if "example.com" in request.url:
            return True
        return False
