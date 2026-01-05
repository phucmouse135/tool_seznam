"""
File demo sử dụng hàm wait_for_code của OnlineSimHelper
Hàm này dùng để chờ và lấy mã OTP từ dịch vụ OnlineSim.io
"""

import asyncio
from utils import OnlineSimHelper, Logger


async def get_code(tzid, timeout=120):
    """
    Hàm chờ và lấy mã code từ OnlineSimHelper.wait_for_code()
    
    :param tzid: Mã giao dịch (transaction ID) lấy từ get_number()
    :param timeout: Thời gian chờ tối đa (giây). Mặc định 120 giây
    :return: Mã code (string) hoặc None nếu timeout
    """
    print("=" * 60)
    print("CHỜ NHẬN MÃ CODE TỪ ONLINE SIM")
    print("=" * 60)
    print(f"\n📋 Transaction ID (tzid): {tzid}")
    print(f"⏱️  Timeout: {timeout} giây\n")
    
    try:
        code = await OnlineSimHelper.wait_for_code(tzid=tzid, timeout=timeout)
        
        if code:
            print(f"\n✅ THÀNH CÔNG!")
            print(f"📱 Mã code: {code}")
            return code
        else:
            print(f"\n❌ Không nhận được mã code (Timeout)")
            return None
            
    except Exception as e:
        print(f"\n❌ Lỗi: {e}")
        return None


async def demo_get_code_with_tzid():
    """
    Ví dụ sử dụng wait_for_code với tzid có sẵn
    """
    print("\n" + "=" * 60)
    print("DEMO: Sử dụng wait_for_code với tzid")
    print("=" * 60)
    
    # Nhập tzid từ người dùng (hoặc hardcode để test)
    tzid = input("\n📝 Nhập Transaction ID (tzid): ").strip()
    
    if not tzid:
        print("❌ Tzid không được để trống!")
        return
    
    # Chờ mã code với timeout mặc định (120 giây)
    code = await get_code(tzid, timeout=120)
    
    if code:
        print(f"\n🎉 Hoàn thành! Mã code: {code}")
    else:
        print(f"\n💔 Không nhận được mã code")


async def demo_full_flow():
    """
    Ví dụ đầy đủ: Lấy số điện thoại -> Chờ mã code
    """
    print("\n" + "=" * 60)
    print("DEMO: Quy trình đầy đủ (Get Number -> Wait Code)")
    print("=" * 60)
    
    service = "seznam"
    country = 420
    
    # Bước 1: Lấy số điện thoại
    print(f"\n📞 Bước 1: Đang lấy số điện thoại cho {service} (country={country})...")
    try:
        result = await OnlineSimHelper.get_number(service=service, country=country)
        if not result:
            print("❌ Không lấy được số điện thoại")
            return
        
        tzid, phone_number = result
        print(f"✅ Đã lấy số: {phone_number}")
        print(f"✅ Transaction ID: {tzid}")
        
        # Bước 2: Chờ mã code
        print(f"\n📨 Bước 2: Đang chờ mã code...")
        code = await OnlineSimHelper.wait_for_code(tzid=tzid, timeout=180)
        
        if code:
            print(f"\n🎉 THÀNH CÔNG!")
            print(f"📱 Số điện thoại: {phone_number}")
            print(f"🔑 Mã code: {code}")
        else:
            print(f"\n❌ Không nhận được mã code")
            
    except Exception as e:
        print(f"❌ Lỗi: {e}")


async def main():
    """
    Hàm main - chọn chế độ chạy
    """
    print("\n" + "=" * 60)
    print("CHƯƠNG TRÌNH LẤY MÃ CODE TỪ ONLINE SIM")
    print("=" * 60)
    print("\nChọn chế độ:")
    print("1. Chờ mã code với tzid có sẵn")
    print("2. Quy trình đầy đủ (Lấy số -> Chờ code)")
    print("3. Thoát")
    
    choice = input("\n👉 Lựa chọn (1/2/3): ").strip()
    
    if choice == "1":
        await demo_get_code_with_tzid()
    elif choice == "2":
        await demo_full_flow()
    elif choice == "3":
        print("👋 Tạm biệt!")
    else:
        print("❌ Lựa chọn không hợp lệ!")


if __name__ == "__main__":
    # Chạy chương trình
    asyncio.run(main())

