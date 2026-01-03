from utils import OnlineSimHelper, Logger, FileManager

tariffs = OnlineSimHelper.get_tariffs()

Logger.info("OnlineSim", "📄 Tariffs JSON:\n" + str(tariffs))
FileManager.append_result("onlinesim_tariffs.json", str(tariffs))

print("✅ Done, services =", len(tariffs.get("services", [])))
