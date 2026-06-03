local Players = game:GetService("Players")
local HttpService = game:GetService("HttpService")
local player = Players.LocalPlayer

print("--- [Hệ Thống] Đang khởi động Script Check Account ---")

-- 1. Kiểm tra sự tồn tại của file cấu hình
if not isfile("blox_fruit.json") then
    warn("[LỖI] Không tìm thấy file 'blox_fruit.json' trong thư mục workspace!")
    return
end

local config_raw = readfile("blox_fruit.json")
local config = HttpService:JSONDecode(config_raw)

-- Normalize: chỉ 3 key này là string số
local num_keys = { Level = true, Beli = true, Fragments = true }
for k, v in pairs(config) do
    if num_keys[k] then
        config[k] = tonumber(v)
    end
end

-- 2. Khởi tạo dữ liệu
local data = player:WaitForChild("Data", 9e9)
local Level = data:WaitForChild("Level", 9e9)
local Beli = data:WaitForChild("Beli", 9e9)
local Fragments = data:WaitForChild("Fragments", 9e9)

getgenv().file_name = player.Name .. ".txt"
getgenv().content = "completed-" .. player.Name

local config_count = 0
for _ in pairs(config) do config_count = config_count + 1 end
print("[INFO] Số lượng yêu cầu cần đạt: " .. config_count)

-- Hàm kiểm tra vật phẩm trong túi đồ
local function check_item(item, inventory)
    if type(inventory) ~= "table" then return false end
    for _, v in pairs(inventory) do
        if v.Name == item then return true end
    end
    return false
end

-- 3. Vòng lặp kiểm tra
while task.wait(30) do
    print("--- [DEBUG] Đang quét điều kiện (" .. os.date("%H:%M:%S") .. ") ---")

    local success = {}
    local inventory = {}
    local Godhuman = false

    -- Lấy Inventory từ Server
    local s_inv, r_inv = pcall(function()
        return game.ReplicatedStorage.Remotes.CommF_:InvokeServer("getInventory")
    end)
    if s_inv then inventory = r_inv else warn("[LỖI] Không thể lấy Inventory") end

    -- Chỉ kiểm tra Godhuman nếu trong config có yêu cầu
    if config["Godhuman"] then
        local s_gh, r_gh = pcall(function()
            return game.ReplicatedStorage.Remotes.CommF_:InvokeServer("BuyGodhuman", true)
        end)
        Godhuman = r_gh == 1
    end

    -- Kiểm tra từng điều kiện trong Config
    for k, v in pairs(config) do
        local matched = false

        if k == "Level" and Level.Value >= v then
            matched = true
        elseif k == "Beli" and Beli.Value >= v then
            matched = true
        elseif k == "Fragments" and Fragments.Value >= v then
            matched = true
        elseif k == "Godhuman" and Godhuman then
            matched = true
        elseif check_item(k, inventory) then
            matched = true
        end

        if matched then
            print("  [+] Đạt điều kiện: " .. k)
            table.insert(success, k)
        else
            print("  [-] Chưa đạt: " .. k)
        end
    end

    print("[TIẾN ĐỘ] Hiện tại: " .. #success .. "/" .. config_count)

    -- 4. Ghi file khi hoàn thành tất cả
    if #success >= config_count then
        print("[THÀNH CÔNG] Đạt mọi điều kiện! Đang ghi file...")
        local s, e = pcall(function()
            writefile(getgenv().file_name, getgenv().content)
        end)

        if not s then
            warn("[LỖI] Không thể ghi file: ", e)
        else
            print("[HỆ THỐNG] Đã hoàn thành ghi file cho: ", player.Name)
            break
        end
    end
end