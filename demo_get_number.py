"""
File demo sử dụng hàm get_number của OnlineSimHelper
Hàm này dùng để lấy số điện thoại từ dịch vụ OnlineSim.io
"""

import asyncio
from utils import OnlineSimHelper, Logger


async def demo_get_number():
    """
    Hàm demo cách sử dụng OnlineSimHelper.get_number()
    """
    print("=" * 60)
    print("DEMO: Sử dụng OnlineSimHelper.get_number()")
    print("=" * 60)
    
    # Ví dụ 1: Lấy số điện thoại cho dịch vụ Google (mặc định country=7)
    print("\n📱 Ví dụ 1: Lấy số điện thoại cho Google (Nga - country=7)")
    try:
        result = await OnlineSimHelper.get_number(service="google", country=7)
        if result:
            tzid, phone_number = result
            print(f"✅ Thành công!")
            print(f"   - Transaction ID (tzid): {tzid}")
            print(f"   - Số điện thoại: {phone_number}")
        else:
            print("❌ Không lấy được số điện thoại")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    print("\n" + "-" * 60)
    
    # Ví dụ 2: Lấy số điện thoại cho dịch vụ Seznam (Czech - country=420)
    print("\n📱 Ví dụ 2: Lấy số điện thoại cho Seznam (Czech - country=420)")
    try:
        result = await OnlineSimHelper.get_number(service="seznam", country=420)
        if result:
            tzid, phone_number = result
            print(f"✅ Thành công!")
            print(f"   - Transaction ID (tzid): {tzid}")
            print(f"   - Số điện thoại: {phone_number}")
        else:
            print("❌ Không lấy được số điện thoại")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    print("\n" + "-" * 60)
    
    # Ví dụ 3: Lấy số điện thoại cho Facebook (Mỹ - country=1)
    print("\n📱 Ví dụ 3: Lấy số điện thoại cho Facebook (Mỹ - country=1)")
    try:
        result = await OnlineSimHelper.get_number(service="facebook", country=1)
        if result:
            tzid, phone_number = result
            print(f"✅ Thành công!")
            print(f"   - Transaction ID (tzid): {tzid}")
            print(f"   - Số điện thoại: {phone_number}")
        else:
            print("❌ Không lấy được số điện thoại")
    except Exception as e:
        print(f"❌ Lỗi: {e}")
    
    print("\n" + "=" * 60)


async def demo_with_retry():
    """
    Ví dụ sử dụng get_number với cơ chế retry (thử lại nhiều lần)
    """
    print("\n" + "=" * 60)
    print("DEMO: Sử dụng get_number với cơ chế Retry")
    print("=" * 60)
    
    service = "seznam"
    country = 420
    max_retries = 3
    
    print(f"\n🔄 Đang thử lấy số điện thoại ({service}, country={country})...")
    print(f"   Số lần thử tối đa: {max_retries}")
    
    tzid = None
    phone_number = None
    
    for attempt in range(max_retries):
        try:
            result = await OnlineSimHelper.get_number(service=service, country=country)
            if result:
                tzid, phone_number = result
                print(f"\n✅ Thành công ở lần thử thứ {attempt + 1}!")
                print(f"   - Transaction ID (tzid): {tzid}")
                print(f"   - Số điện thoại: {phone_number}")
                break
            else:
                print(f"⚠️ Lần thử {attempt + 1}/{max_retries} thất bại. Đang thử lại...")
        except Exception as e:
            print(f"⚠️ Lần thử {attempt + 1}/{max_retries} lỗi: {e}")
            if attempt < max_retries - 1:
                print(f"   Đợi 2 giây trước khi thử lại...")
                await asyncio.sleep(2)
    
    if not tzid:
        print(f"\n❌ Đã thử {max_retries} lần nhưng không lấy được số điện thoại")
    
    print("\n" + "=" * 60)


async def main():
    """
    Hàm main chạy các demo
    """
    # Chạy demo cơ bản
    await demo_get_number()
    
    # Chạy demo với retry (uncomment dòng dưới nếu muốn chạy)
    # await demo_with_retry()


if __name__ == "__main__":
    # Chạy các hàm async
    asyncio.run(main())

