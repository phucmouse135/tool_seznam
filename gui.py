import customtkinter as ctk
from tkinter import ttk, filedialog, messagebox
import threading
import asyncio
from playwright.async_api import async_playwright
from utils import Logger, ProxyManager, BrowserUtils, DataHelper, FileManager, OnlineSimHelper
from config import Config

# --- CẤU HÌNH UI ---
ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class AutomationApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Register Seznam Auto")
        self.geometry("1100x700")

        # --- VARIABLES ---
        self.api_sim_var = ctk.StringVar(value=OnlineSimHelper.API_KEY)
        self.api_proxy_var = ctk.StringVar(value=Config.PROXY_API_BASE)
        self.thread_count_var = ctk.StringVar(value=str(Config.NUM_THREADS))
        self.input_format_var = ctk.StringVar(value="email|pass")
        self.is_running = False
        self.stop_event = threading.Event()
        self.tasks = []
        self.loop = None
        self.thread_obj = None

        # --- LAYOUT ---
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(2, weight=1) # Table area expands

        # 1. CONFIG FRAME
        self.create_config_frame()

        # 2. ACTION BUTTONS
        self.create_action_buttons()

        # 3. DATA TABLE
        self.create_data_table()

        # 4. CONTROL FRAME
        self.create_control_frame()

    def create_config_frame(self):
        frame = ctk.CTkFrame(self)
        frame.grid(row=0, column=0, padx=10, pady=10, sticky="ew")
        frame.grid_columnconfigure(1, weight=1)

        # API OnlineSim
        ctk.CTkLabel(frame, text="API OnlineSim:").grid(row=0, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.api_sim_var).grid(row=0, column=1, padx=5, pady=5, sticky="ew")

        # API 9Proxy
        ctk.CTkLabel(frame, text="API 9Proxy:").grid(row=1, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.api_proxy_var).grid(row=1, column=1, padx=5, pady=5, sticky="ew")

        # Threads
        ctk.CTkLabel(frame, text="Số luồng:").grid(row=2, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.thread_count_var).grid(row=2, column=1, padx=5, pady=5, sticky="ew")

        # Input Format
        ctk.CTkLabel(frame, text="Định dạng Input:").grid(row=3, column=0, padx=5, pady=5, sticky="w")
        ctk.CTkEntry(frame, textvariable=self.input_format_var).grid(row=3, column=1, padx=5, pady=5, sticky="ew")
        ctk.CTkLabel(frame, text="(Ví dụ: email|pass hoặc pass|email)").grid(row=3, column=2, padx=5, pady=5, sticky="w")

    def create_action_buttons(self):
        frame = ctk.CTkFrame(self, fg_color="transparent")
        frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")

        ctk.CTkButton(frame, text="Import File", command=self.import_file).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="Thêm vào bảng", command=self.add_manual).pack(side="left", padx=5)
        ctk.CTkButton(frame, text="Xóa toàn bộ bảng", command=self.clear_table, fg_color="red").pack(side="left", padx=5)
        ctk.CTkButton(frame, text="Xóa hàng đã chọn", command=self.delete_selected, fg_color="orange").pack(side="left", padx=5)

    def create_data_table(self):
        # CustomTkinter chưa có Table native ngon, dùng Treeview của ttk
        # Wrap trong Frame để chỉnh style
        frame = ctk.CTkFrame(self)
        frame.grid(row=2, column=0, padx=10, pady=5, sticky="nsew")
        
        # Style cho Treeview dark mode
        style = ttk.Style()
        style.theme_use("default")
        style.configure("Treeview", 
                        background="#2b2b2b", 
                        foreground="white", 
                        fieldbackground="#2b2b2b", 
                        rowheight=25)
        style.map('Treeview', background=[('selected', '#1f538d')])
        style.configure("Treeview.Heading", background="#333333", foreground="white")

        columns = ("stt", "email", "pass", "phone", "status")
        self.tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="extended")
        
        self.tree.heading("stt", text="STT")
        self.tree.heading("email", text="Email")
        self.tree.heading("pass", text="Pass")
        self.tree.heading("phone", text="SĐT")
        self.tree.heading("status", text="Status")

        self.tree.column("stt", width=50, anchor="center")
        self.tree.column("email", width=250)
        self.tree.column("pass", width=150)
        self.tree.column("phone", width=150)
        self.tree.column("status", width=150)

        # Scrollbar
        scrollbar = ttk.Scrollbar(frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscroll=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")

    def create_control_frame(self):
        frame = ctk.CTkFrame(self, height=50)
        frame.grid(row=3, column=0, padx=10, pady=10, sticky="ew")

        self.btn_start = ctk.CTkButton(frame, text="Start", command=self.on_start_click, fg_color="green")
        self.btn_start.pack(side="left", padx=10, pady=10)

        self.btn_end = ctk.CTkButton(frame, text="End", command=self.on_stop_click, fg_color="darkred", state="disabled")
        self.btn_end.pack(side="left", padx=10, pady=10)

        self.lbl_progress = ctk.CTkLabel(frame, text="Tiến trình: 0/0")
        self.lbl_progress.pack(side="right", padx=20)

    # --- LOGIC HANDLERS ---

    def parse_input_line(self, line, format_str):
        try:
            if not line:
                return None, None
            
            # Determine delimiter (default |)
            delimiter = "|"
            if ";" in format_str:
                delimiter = ";"
            elif "," in format_str:
                delimiter = ","
            
            # Split format and line
            fmt_parts = [x.strip().lower() for x in format_str.split(delimiter)]
            line_parts = [x.strip() for x in line.split(delimiter)]
            
            if not fmt_parts:
                return None, None
            
            data = {}
            for i, key in enumerate(fmt_parts):
                if i < len(line_parts):
                    data[key] = line_parts[i]
            
            # Extract email/pass based on common keys
            email = data.get("email") or data.get("user") or data.get("username") or ""
            pwd = data.get("pass") or data.get("password") or data.get("pwd") or ""
            
            # Fallback if format is just one column or mapping failed but we have parts
            if not email and len(line_parts) > 0:
                email = line_parts[0]
            if not pwd and len(line_parts) > 1:
                pwd = line_parts[1]
            
            return email, pwd
        except Exception:
            return None, None

    def import_file(self):
        file_path = filedialog.askopenfilename(filetypes=[("Text Files", "*.txt")])
        if file_path:
            lines = FileManager.read_lines(file_path)
            format_str = self.input_format_var.get()
            for line in lines:
                email, pwd = self.parse_input_line(line, format_str)
                if email:
                    self.add_row(email, pwd)
            self.update_progress_label()

    def add_manual(self):
        format_str = self.input_format_var.get()
        dialog = ctk.CTkInputDialog(text=f"Nhập theo định dạng: {format_str}", title="Thêm thủ công")
        text = dialog.get_input()
        if text:
            email, pwd = self.parse_input_line(text, format_str)
            if email:
                self.add_row(email, pwd)
            self.update_progress_label()

    def add_row(self, email, pwd):
        idx = len(self.tree.get_children()) + 1
        self.tree.insert("", "end", values=(idx, email, pwd, "", "Pending"))

    def clear_table(self):
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.update_progress_label()

    def delete_selected(self):
        selected_items = self.tree.selection()
        for item in selected_items:
            self.tree.delete(item)
        self.update_progress_label()

    def update_progress_label(self):
        total = len(self.tree.get_children())
        # Đếm số dòng đã xong (Success/Failed)
        done = 0
        for item in self.tree.get_children():
            status = self.tree.item(item, "values")[4]
            if status in ["Success", "Failed"] or "Failed" in status:
                done += 1
        self.lbl_progress.configure(text=f"Tiến trình: {done}/{total}")

    def on_start_click(self):
        if self.is_running:
            return

        # Validate inputs
        try:
            num_threads = int(self.thread_count_var.get())
        except ValueError:
            messagebox.showerror("Lỗi", "Số luồng phải là số nguyên!")
            return

        # Update Config globals (Hack nhẹ để truyền tham số vào utils/config)
        OnlineSimHelper.API_KEY = self.api_sim_var.get()
        # Config.PROXY_API_BASE = self.api_proxy_var.get() # Cần sửa utils để dùng biến này động
        # Config.NUM_THREADS = num_threads

        # Get data from table
        items = self.tree.get_children()
        data_list = []
        for item_id in items:
            vals = self.tree.item(item_id, "values")
            # Chỉ lấy những dòng chưa chạy (Pending)
            if vals[4] == "Pending":
                data_list.append({
                    "id": item_id,
                    "email": vals[1],
                    "pass": vals[2]
                })
        
        if not data_list:
            messagebox.showinfo("Info", "Không có dữ liệu 'Pending' để chạy!")
            return

        self.is_running = True
        self.stop_event.clear()
        self.btn_start.configure(state="disabled")
        self.btn_end.configure(state="normal")

        # Start Thread
        self.thread_obj = threading.Thread(target=self.run_async_loop, args=(data_list, num_threads))
        self.thread_obj.start()

    def on_stop_click(self):
        if not self.is_running:
            return
        
        # Force focus to ensure popup is seen
        self.focus_force()
        
        if messagebox.askyesno("Xác nhận", "Bạn có chắc muốn dừng tiến trình?", parent=self):
            self.stop_event.set()
            
            # Cancel tasks
            if self.loop and self.loop.is_running():
                self.loop.call_soon_threadsafe(self.cancel_all_tasks)
            
            self.is_running = False
            self.btn_start.configure(state="normal")
            self.btn_end.configure(state="disabled")
            Logger.info("System", "Đã gửi lệnh dừng...")

    def cancel_all_tasks(self):
        for task in self.tasks:
            if not task.done():
                task.cancel()

    def run_async_loop(self, data_list, num_threads):
        self.loop = asyncio.new_event_loop()
        asyncio.set_event_loop(self.loop)
        self.loop.run_until_complete(self.main_logic(data_list, num_threads))
        self.loop.close()
        
        # Reset UI sau khi chạy xong
        self.after(0, lambda: self.btn_start.configure(state="normal"))
        self.after(0, lambda: self.btn_end.configure(state="disabled"))
        self.is_running = False

    # --- CORE LOGIC (Adapted from main.py) ---
    async def main_logic(self, data_list, num_threads):
        semaphore = asyncio.Semaphore(max(1, num_threads))
        
        # Chia chunk
        chunks = DataHelper.chunk_data(data_list, num_threads)
        self.tasks = []
        base_port = Config.BASE_PORT

        for i in range(len(chunks)):
            port = base_port + i
            task = asyncio.create_task(self.worker_ui(i+1, port, semaphore, chunks[i]))
            self.tasks.append(task)

        try:
            await asyncio.gather(*self.tasks)
        except asyncio.CancelledError:
            Logger.info("System", "Tasks cancelled.")
        except Exception as e:
            Logger.error("System", f"Main logic error: {e}")

    async def worker_ui(self, thread_id, port, semaphore, data_chunk):
        async with semaphore:
            Logger.info(thread_id, f"🚀 Worker UI Start Port {port}")
            
            try:
                # BẮT BUỘC: xoay IP (có verify) trước khi chạy tác vụ
                await ProxyManager.ensure_rotated_ip(port, thread_id=thread_id, force_rotate=True)

                async with async_playwright() as p:
                    browser = await p.chromium.launch(headless=False, args=BrowserUtils.get_launch_args())
                    
                    for item in data_chunk:
                        if self.stop_event.is_set():
                            Logger.warning(thread_id, "🛑 Stop Signal Received!")
                            break

                        item_id = item["id"]
                        username = item["email"]
                        password = item["pass"]
                        
                        # Update UI: Running
                        self.update_row_status(item_id, "Running...", "")

                        phone_number = ""
                        failed_reason = ""
                        isOk = False

                        # BẮT BUỘC: xoay IP (có verify) trước khi làm bất kỳ thao tác nào cho acc
                        await ProxyManager.ensure_rotated_ip(port, thread_id=thread_id)

                        # Retry Loop
                        for attempt in range(Config.RETRY_LIMIT):
                            if self.stop_event.is_set():
                                break
                            context = None
                            try:
                                self.update_row_status(item_id, f"Running ({attempt+1})...", "")
                                
                                # --- LOGIC TỪ MAIN.PY ---
                                context, page = await BrowserUtils.create_stealth_context(
                                    browser, port,
                                    Config.TARGET_CONFIG["timezone"],
                                    Config.TARGET_CONFIG["locale"],
                                    Config.TARGET_CONFIG["geolocation"]
                                )
                                
                                # Goto
                                await page.goto("https://registrace.seznam.cz/?service=ucet&return_url=https%3A%2F%2Fucet.seznam.cz", timeout=60000)
                                await page.wait_for_load_state("networkidle")

                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=2)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")

                                # Click Register
                                reg_btn = page.locator("#register form.intro button.official")
                                if await reg_btn.is_visible(timeout=10000):
                                    await reg_btn.click()

                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=2)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")
                                
                                # Fill Form
                                input_username = page.locator("#register-username")
                                await input_username.click()
                                await input_username.press("Control+A")
                                await input_username.press("Backspace")
                                await input_username.press_sequentially(username, delay=100)
                                await BrowserUtils.random_sleep(1, 2)

                                # Email taken (CZ) right after entering username/email
                                email_error_locator = page.locator("div.error:visible")
                                for _ in range(20):  # ~5s
                                    if await email_error_locator.count() > 0:
                                        try:
                                            email_err_txt = (await email_error_locator.first.inner_text()).strip()
                                        except Exception:
                                            email_err_txt = ""
                                        if email_err_txt and "adresa je obsazen" in email_err_txt.lower():
                                            raise Exception(f"EMAIL_TAKEN: {email_err_txt}")
                                        break
                                    await asyncio.sleep(0.25)

                                input_password = page.locator("#register > form.main > label.magic.password.errorable > input[type=password]")
                                await input_password.fill("")
                                await input_password.press_sequentially(password, delay=100)
                                await BrowserUtils.random_sleep(1, 2)
                                
                                await page.keyboard.press("Enter")
                                await page.wait_for_load_state("networkidle")
                                await BrowserUtils.random_sleep(1, 2)

                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=2)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")

                                # Get Phone
                                if not phone_number:
                                    self.update_row_status(item_id, "Get Phone...", "")
                                    # Retry get number logic
                                    tzid = None
                                    for _retry in range(10):
                                        if self.stop_event.is_set():
                                            break
                                        result = await OnlineSimHelper.get_number(service="seznam", country=420)
                                        if result:
                                            tzid, phone_number = result
                                            break
                                        await asyncio.sleep(2)
                                    
                                    if not tzid:
                                        raise Exception("Get Phone Failed (10 tries)")
                                    
                                    # Update Phone to UI
                                    self.update_row_phone(item_id, phone_number)

                                # Fill Phone
                                input_phone = page.locator("#register > form.phone > label.magic.phone.errorable > input[type=text]")
                                await input_phone.fill("")
                                await input_phone.press_sequentially(phone_number, delay=100)
                                await page.keyboard.press("Enter")
                                try:
                                    await page.wait_for_load_state("networkidle", timeout=5000)
                                except Exception:
                                    pass

                                # Check anti-bot popup (có thể hiện trễ) => poll mạnh hơn + selector rộng
                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=10)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")
                                
                                # Check SMS spam limit (CZ/EN) - không bắt bừa mọi div.error
                                error_locator = page.locator("div.error:visible")
                                for _ in range(20):  # ~5s
                                    if await error_locator.count() > 0:
                                        txt = (await error_locator.first.inner_text()).strip()
                                        t = txt.lower()
                                        is_sms_limit = (
                                            ("příliš" in t and "sms" in t and ("24h" in t or "24 h" in t))
                                            or ("too many" in t and "sms" in t and "24" in t)
                                        )
                                        if is_sms_limit:
                                            raise Exception(f"SMS_SPAM_LIMIT: {txt}")
                                        # Nếu là lỗi khác thì không coi là spam-limit ở đây
                                        break
                                    await asyncio.sleep(0.25)

                                # Wait Code
                                self.update_row_status(item_id, "Waiting Code...", phone_number)
                                code = await OnlineSimHelper.wait_for_code(tzid, timeout=180)
                                if not code:
                                    # Try resend
                                    resend_btn = page.locator("#register > form.phone > label.magic.pin.errorable > a")
                                    if await resend_btn.is_visible(timeout=5000):
                                        await resend_btn.click()
                                        code = await OnlineSimHelper.wait_for_code(tzid, timeout=180)
                                
                                if not code:
                                    raise Exception("NO_CODE: OTP timeout")

                                # Fill Code
                                input_code = page.locator("#register > form.phone-verification > label.magic.code.errorable > input[type=text]")
                                await input_code.fill("")
                                await input_code.press_sequentially(code, delay=100)
                                await page.keyboard.press("Enter")
                                try:
                                    await page.wait_for_load_state("networkidle", timeout=5000)
                                except Exception:
                                    pass

                                # Popup anti-bot cũng có thể xuất hiện sau khi submit OTP (poll mạnh hơn)
                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=10)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")

                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=2)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")

                                # Final Steps
                                agree_btn = page.locator("button[data-action='ok']")
                                if await agree_btn.is_visible(timeout=10000):
                                    await agree_btn.click()

                                pop = await BrowserUtils.detect_antibot_popup(page, timeout_seconds=2)
                                if pop:
                                    raise Exception(f"IP_BANNED: {pop}")
                                
                                back_btn = page.locator("button.back[data-locale='back_to_inbox']")
                                if await back_btn.is_visible(timeout=10000):
                                    await back_btn.click()

                                # SUCCESS
                                isOk = True
                                FileManager.append_result("data/success.txt", f"{username}|{password}|{phone_number}|Success")
                                self.update_row_status(item_id, "Success", phone_number)
                                await context.close()
                                break # Exit retry loop

                            except asyncio.CancelledError:
                                raise # Re-raise to outer try/except
                            except Exception as e:
                                Logger.error(thread_id, f"Error: {e}")
                                failed_reason = str(e)
                                if context:
                                    await context.close()

                                # Timeout => bỏ qua email hiện tại (không retry / không rotate)
                                if "Timeout" in failed_reason:
                                    failed_reason = "TIMEOUT"
                                    break

                                # Không retry các lỗi không thể cứu bằng đổi IP
                                if "NO_CODE" in failed_reason:
                                    break
                                if "EMAIL_TAKEN" in failed_reason:
                                    break
                                if "SMS_SPAM_LIMIT" in failed_reason:
                                    break
                                if "Get Phone Failed" in failed_reason:
                                    break
                                
                                # Rotate IP if needed
                                if "IP_BANNED" in str(e):
                                    self.update_row_status(item_id, "Rotating IP...", phone_number)
                                    await ProxyManager.ensure_rotated_ip(port, thread_id=thread_id, force_rotate=True)
                                    await BrowserUtils.random_sleep(3, 5)

                        if not isOk:
                            FileManager.append_result("data/failed.txt", f"{username}|{password}|{phone_number}|Failed|{failed_reason}")
                            self.update_row_status(item_id, f"Failed: {failed_reason}", phone_number)
                        
                        self.after(0, self.update_progress_label)

                    await browser.close()
            except asyncio.CancelledError:
                Logger.warning(thread_id, "🛑 Worker bị hủy (Cancelled)!")
            except Exception as e:
                Logger.error(thread_id, f"Worker Fatal Error: {e}")

    def update_row_status(self, item_id, status, phone):
        # Tkinter không thread-safe, phải dùng after hoặc queue. 
        # Tuy nhiên update đơn giản trên Treeview thường ok, nhưng tốt nhất là wrap.
        def _update():
            self.tree.set(item_id, "status", status)
            if phone:
                self.tree.set(item_id, "phone", phone)
            
            # Color coding
            tags = []
            if "Success" in status:
                tags = ("success",)
            elif "Failed" in status:
                tags = ("failed",)
            elif "Running" in status:
                tags = ("running",)
            
            # Treeview tag config (cần set ở init hoặc đây)
            self.tree.tag_configure("success", foreground="#00ff00")
            self.tree.tag_configure("failed", foreground="#ff5555")
            self.tree.tag_configure("running", foreground="#55aaff")
            
            self.tree.item(item_id, tags=tags)

        self.after(0, _update)

    def update_row_phone(self, item_id, phone):
        self.after(0, lambda: self.tree.set(item_id, "phone", phone))

if __name__ == "__main__":
    app = AutomationApp()
    app.mainloop()
