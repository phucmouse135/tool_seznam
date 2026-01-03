import asyncio
import random
import time
import json
import os
from datetime import datetime
import requests
from playwright.async_api import async_playwright, Page, BrowserContext
from playwright_stealth import stealth

# --- CONSTANTS (CẤU HÌNH CHUNG) ---
PROXY_API_URL = "http://127.0.0.1:10101/api/proxy"
DEFAULT_USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
VIEWPORT_SIZE = {"width": 1920, "height": 1080}
ONLINE_SIM_API_KEY = os.getenv("ONLINE_SIM_API_KEY")

class Logger:
    """Class quản lý việc in log ra màn hình cho đẹp và dễ debug đa luồng"""
    
    @staticmethod
    def log(thread_id: int | str, message: str, level: str = "INFO"):
        """
        Format: [TIME] [Thread-ID] [LEVEL] Message
        Example: [12:00:00] [Thread-1] [INFO] Login success
        """
        current_time = datetime.now().strftime("%H:%M:%S")
        
        # Màu sắc cho terminal (ANSI codes)
        colors = {
            "INFO": "\033[94m",    # Blue
            "SUCCESS": "\033[92m", # Green
            "ERROR": "\033[91m",   # Red
            "WARNING": "\033[93m", # Yellow
            "RESET": "\033[0m"
        }
        
        color = colors.get(level, colors["RESET"])
        print(f"{colors['RESET']}[{current_time}] [Thread-{thread_id}] {color}[{level}] {message}{colors['RESET']}")

    @staticmethod
    def info(tid, msg): Logger.log(tid, msg, "INFO")
    @staticmethod
    def success(tid, msg): Logger.log(tid, msg, "SUCCESS")
    @staticmethod
    def error(tid, msg): Logger.log(tid, msg, "ERROR")
    @staticmethod
    def warning(tid, msg): Logger.log(tid, msg, "WARNING")


class ProxyManager:
    """Class chuyên xử lý logic liên quan đến 9Proxy"""
    
    @staticmethod
    def rotate_ip(port: int, country: str = "CZ", thread_id: int = 0) -> bool:
        """
        Gọi API để đổi IP cho port chỉ định.
        Trả về True nếu thành công, False nếu thất bại.
        """
        Logger.info(thread_id, f"♻️ Đang yêu cầu đổi IP {country} cho Port {port}...")
        
        params = {
            "t": 2,          # Type (thường là 2 với 9Proxy)
            "num": 1,        # Số lượng IP
            "port": port,    # Port cần đổi
            "country": country
        }
        
        try:
            # Timeout 10s để tránh treo tool nếu API lỗi
            resp = requests.get(PROXY_API_URL, params=params, timeout=10)
            
            if resp.status_code == 200:
                # 9Proxy trả về JSON, ta có thể check thêm field code/msg nếu cần
                # Quan trọng: Chờ 3s để tunnel được thiết lập
                time.sleep(3) 
                Logger.success(thread_id, f"✅ Đã đổi IP xong (Port {port})")
                return True
            else:
                Logger.error(thread_id, f"❌ API Error: {resp.status_code} - {resp.text}")
                return False
        except Exception as e:
            Logger.error(thread_id, f"❌ Lỗi kết nối 9Proxy: {str(e)}")
            return False

    @staticmethod
    def get_local_proxy_url(port: int) -> str:
        return f"http://127.0.0.1:{port}"


class BrowserUtils:
    """Class cấu hình Browser và Context (Stealth, Anti-Detect)"""

    @staticmethod
    def get_launch_args() -> list:
        """Trả về list các arguments để ẩn dấu hiệu Automation"""
        return [
            "--disable-blink-features=AutomationControlled", # Quan trọng nhất
            # "--no-sandbox",
            "--disable-infobars", # Ẩn thanh thông báo trình duyệt
            # "--disable-setuid-sandbox", # An toàn hơn trên Linux
            "--ignore-certificate-errors", # Bỏ qua lỗi SSL
            "--disable-gpu", # Giúp nhẹ máy hơn
            "--window-size=1920,1080"
        ]

    @staticmethod
    async def create_stealth_context(browser, port: int, timezone: str , locale: str, geolocation: dict) -> tuple[BrowserContext, Page]:
        """
        Tạo Context + Page đã được tiêm Stealth và config Proxy.
        Return: (context, page)
        """
        proxy_url = ProxyManager.get_local_proxy_url(port)
        
        context = await browser.new_context(
            proxy={"server": proxy_url},
            viewport=VIEWPORT_SIZE,
            user_agent=DEFAULT_USER_AGENT,
            locale=locale,
            timezone_id=timezone,
            permissions=["geolocation"], # Cấp quyền vị trí để trông thật hơn
            geolocation=geolocation,
        )
        
        page = await context.new_page()
        
        # Kích hoạt Anti-Detect Stealth
        print("🕵️‍♂️ Thiết lập Stealth cho Page...")
        # stealth(page)
        print("✅ Stealth đã được thiết lập.")        
        return context, page

    @staticmethod
    async def random_sleep(min_s: float = 1.0, max_s: float = 3.0):
        """Ngủ ngẫu nhiên để giả lập hành vi người dùng"""
        sleep_time = random.uniform(min_s, max_s)
        await asyncio.sleep(sleep_time)
        
    @staticmethod
    async def block_resources(page: Page):
        """Chặn tải các tài nguyên không cần thiết như hình ảnh, CSS để tăng tốc độ"""
        async def route_intercept(route, request):
            if request.resource_type in ["image", "stylesheet", "font"]:
                await route.abort()
            else:
                await route.continue_()
        
        await page.route("**/*", route_intercept)
    



class FileManager:
    """Class xử lý đọc/ghi file"""

    @staticmethod
    def read_lines(filepath: str) -> list:
        """Đọc file text, trả về list các dòng (đã strip whitespace)"""
        if not os.path.exists(filepath):
            return []
        with open(filepath, "r", encoding="utf-8") as f:
            return [line.strip() for line in f if line.strip()]

    @staticmethod
    def append_result(filepath: str, content: str):
        """Ghi nối tiếp kết quả vào file (Thread-safe ở mức cơ bản)"""
        try:
            with open(filepath, "a", encoding="utf-8") as f:
                f.write(content + "\n")
        except Exception as e:
            print(f"Lỗi ghi file: {e}")
    
    @staticmethod
    def delete_browser_data(thread_id: int, port: int):
        """Xóa dữ liệu trình duyệt để tránh cache
        data_path = f"browser_data/thread_{thread_id}_port_{port}"
        """
        data_path = f"browser_data/thread_{thread_id}_port_{port}"
        if os.path.exists(data_path):
            try:
                import shutil
                shutil.rmtree(data_path)
                Logger.info(thread_id, f"🗑️ Đã xóa dữ liệu trình duyệt tại {data_path}")
            except Exception as e:
                Logger.error(thread_id, f"❌ Lỗi xóa dữ liệu trình duyệt: {e}")
        else:
            Logger.info(thread_id, f"ℹ️ Không tìm thấy dữ liệu trình duyệt tại {data_path} để xóa")

class DataHelper:
    """Các hàm xử lý dữ liệu nhỏ lẻ"""
    
    @staticmethod
    def extract_between(text: str, start_str: str, end_str: str) -> str:
        """Hàm lấy chuỗi nằm giữa 2 chuỗi khác (Giống StringUtils trong Java)"""
        try:
            start = text.index(start_str) + len(start_str)
            end = text.index(end_str, start)
            return text[start:end]
        except ValueError:
            return ""

    @staticmethod
    def random_string(length=8):
        import string
        letters = string.ascii_lowercase + string.digits
        return ''.join(random.choice(letters) for i in range(length))

    @staticmethod
    def chunk_data(data_list: list, num_chunks: int) -> list:
        """Chia nhỏ danh sách data thành các chunk để phân phối cho các thread"""
        avg = len(data_list) / float(num_chunks)
        chunks = []
        last = 0.0

        while last < len(data_list):
            chunks.append(data_list[int(last):int(last + avg)])
            last += avg

        return chunks

# CALL API 
class APIClient:
    """Class xử lý các cuộc gọi API chung"""
    
    @staticmethod
    def get_json(url: str, params: dict = {}, headers: dict = {}, timeout: int = 10) -> dict | None:
        """Gọi API GET và trả về JSON (hoặc None nếu lỗi)"""
        try:
            resp = requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API GET Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"API GET Exception: {str(e)}")
            return None
    @staticmethod
    def post_json(url: str, data: dict = {}, headers: dict = {}, timeout: int = 10) -> dict | None:
        """Gọi API POST và trả về JSON (hoặc None nếu lỗi)"""
        try:
            resp = requests.post(url, json=data, headers=headers, timeout=timeout)
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"API POST Error: {resp.status_code} - {resp.text}")
                return None
        except Exception as e:
            print(f"API POST Exception: {str(e)}")
            return None
        
class OnlineSimHelper:
    """Helper chuyên xử lý API OnlineSim.io"""
    
    BASE_URL_GET_NUM = "https://onlinesim.io/api/getNum.php"
    BASE_URL_GET_STATE = "https://onlinesim.io/api/getState.php"
    BASE_URL_GET_TARIFFS = "https://onlinesim.io/api/getTariffs.php"
    API_KEY ="YZns5KgF44YsTw6-NKT1G6v6-6EQ5N5sG-V1AgA5t7-aTgr7BuWAtAbF94"  # Thay bằng API Key thực của bạn
    
    def __init__(self):
        if not self.API_KEY:
            raise ValueError("ONLINE_SIM_API_KEY is not set in environment variables.")
        
 
    @staticmethod   
    def get_number(service="google", country=7):
        """
        Bước 1: Lấy số điện thoại mới.
        :param service: Tên dịch vụ (ví dụ: 'google', 'facebook', 'telegram')
        :param country: Mã quốc gia (ví dụ: 7 là Nga, 1 là Mỹ, 84 là VN - tuỳ list của họ)
        :return: (tzid, phone_number) hoặc raise Exception
        """
        params = {
            "apikey": OnlineSimHelper.API_KEY,
            "service": service,
            "country": country,
            "number": "true" # Để hiển thị số ngay lập tức
        }
        Logger.info("OnlineSim", f"📞 Yêu cầu số điện thoại cho dịch vụ '{service}' ở quốc gia {country}...")
        
        
        try:
            resp = requests.get(OnlineSimHelper.BASE_URL_GET_NUM, params=params, timeout=10000)
            data = resp.json()
            
            # Check response theo tài liệu: response == 1 là thành công
            if data.get("response") != 1:
                # Nếu response != 1, nó thường trả về chuỗi lỗi (vd: "WARNING_NO_NUMS")
                error_msg = data.get("response") 
                Logger.error("OnlineSim", f"❌ Lấy số thất bại: {error_msg}")
                raise Exception(f"Get Number Failed: {error_msg}")
            
            tzid = data.get("tzid")
            phone_number = data.get("number")
            # API trả về có thể không có key 'number' ngay ở cấp 1 tuỳ format, 
            # nhưng theo doc bạn đưa thì nếu number=true sẽ hiện.
            # Lưu ý: Cần kiểm tra kỹ response thực tế, đôi khi nó nằm trong object khác.
            # Ở đây giả định data trả về dạng: {"response":1, "tzid":123, "number":"+12345"}
            # Nếu api trả về chỉ có tzid, bạn phải gọi getState 1 lần để lấy số. 
            # Tuy nhiên tham số number=true thường sẽ trả về luôn.
            
            # Để chắc chắn, tôi return tzid. Số điện thoại có thể lấy ở bước getState nếu ở đây thiếu.
            return (tzid, phone_number)
            
        except Exception as e:
            print(f"❌ Error calling OnlineSim: {e}")
            return None

    @staticmethod
    def wait_for_code(tzid, timeout=120):
        """
        Bước 2: Chờ nhận OTP (Cơ chế Polling).
        :param tzid: Mã giao dịch lấy từ bước 1.
        :param timeout: Thời gian chờ tối đa (giây).
        :return: Code (string) hoặc None nếu timeout.
        """
        start_time = time.time()
        
        print(f"⏳ Đang chờ SMS cho GD {tzid} (Timeout: {timeout}s)...")
        
        while time.time() - start_time < timeout:
            params = {
                "apikey": OnlineSimHelper.API_KEY,
                "tzid": tzid,
                "message_to_code": 1, # QUAN TRỌNG: 1 = Chỉ lấy Code, 0 = Lấy cả tin nhắn
                "msg_list": 0         # 0 = Chỉ lấy tin nhắn active
            }
            
            try:
                resp = requests.get(OnlineSimHelper.BASE_URL_GET_STATE, params=params, timeout=10)
                data = resp.json() 
                # API này trả về 1 List Array: [{"response": "TZ_NUM_WAIT", ...}]
                
                if isinstance(data, list) and len(data) > 0:
                    item = data[0] # Lấy giao dịch đầu tiên
                    status = item.get("response")
                    
                    # --- XỬ LÝ TRẠNG THÁI ---
                    if status == "TZ_NUM_ANSWER":
                        # ✅ Đã có tin nhắn
                        code = item.get("msg").strip() # Do message_to_code=1 nên field này là code
                        code = code[-code.rfind(" ")-4:code.rfind(" ")]
                        print(f"✅ Đã nhận Code: {code}")
                        return code
                    
                    elif status == "TZ_NUM_WAIT":
                        # ⏳ Vẫn đang chờ -> Không làm gì cả, chờ loop tiếp
                        pass
                    
                    elif status == "TZ_OVER_OK":
                        print("⚠️ Giao dịch đã bị đóng (Timeout từ phía server sim).")
                        return None
                    
                    else:
                        # Các lỗi khác (NO_NUMS, ERROR...)
                        print(f"⚠️ Trạng thái lạ: {status}")
                
                # Nếu chưa có code, lấy thông tin số điện thoại (nếu bước 1 chưa lấy được)
                # item.get("number") sẽ có ở đây.
                
            except Exception as e:
                print(f"⚠️ Lỗi kết nối API check code: {e}")

            # Ngủ 3 giây rồi hỏi lại (tránh spam nát API của họ)
            time.sleep(5)
            
        print("❌ Hết thời gian chờ (Timeout).")
        return None

    @staticmethod
    def get_tariffs(
        country: int | None = None,
        service: str | None = None,
        page: int = 1,
        count: int = 50,
        locale_price: int = 0,
        lang: str = "ru",
    ):
        """
        Lấy bảng giá / số lượng SIM theo quốc gia & dịch vụ

        :param country: mã quốc gia (vd: 420)
        :param service: tên service (vd: 'seznam.cz', 'google')
        :param page: trang
        :param count: số item mỗi trang
        :param locale_price: 1 = hiển thị giá theo tiền tệ địa phương
        :param lang: ngôn ngữ response
        :return: dict (raw JSON)
        """

        params = {
            "apikey": OnlineSimHelper.API_KEY,
            "page": page,
            "count": count,
            "locale_price": locale_price,
            "lang": lang,
        }

        if country is not None:
            params["country"] = country
            params["filter_country"] = country

        if service:
            params["filter_service"] = service

        resp = requests.get(
            OnlineSimHelper.BASE_URL_GET_TARIFFS,
            params=params,
            timeout=60
        )

        # Debug khi lỗi HTTP
        if resp.status_code != 200:
            raise Exception(f"HTTP {resp.status_code}: {resp.text[:300]}")

        try:
            data = resp.json()
        except Exception:
            raise Exception(f"Non-JSON response: {resp.text[:300]}")

        return data