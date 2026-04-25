local CoreGui = game:GetService("CoreGui")
local RunService = game:GetService("RunService")

if CoreGui:FindFirstChild("OnlyFPS_Display") then
    CoreGui.OnlyFPS_Display:Destroy()
end

local gui = Instance.new("ScreenGui")
gui.Name = "OnlyFPS_Display"
gui.Parent = CoreGui

local fpsLabel = Instance.new("TextLabel")
fpsLabel.Parent = gui
fpsLabel.Position = UDim2.new(0, 10, 0, 10)
fpsLabel.Size = UDim2.new(0, 100, 0, 30)
fpsLabel.BackgroundTransparency = 1
fpsLabel.Font = Enum.Font.GothamBold
fpsLabel.TextSize = 22
fpsLabel.TextXAlignment = Enum.TextXAlignment.Left
fpsLabel.TextYAlignment = Enum.TextYAlignment.Top
fpsLabel.TextStrokeTransparency = 0.4
fpsLabel.TextStrokeColor3 = Color3.new(0, 0, 0)

-- Biến theo dõi để tính FPS mỗi 1 giây
local frameCount = 0
local elapsed = 0

RunService.RenderStepped:Connect(function(deltaTime)
    -- Đếm frame và thời gian tích lũy
    frameCount += 1
    elapsed += deltaTime

    -- Chỉ cập nhật text FPS mỗi 1 giây
    if elapsed >= 1 then
        fpsLabel.Text = "FPS: " .. frameCount
        frameCount = 0
        elapsed -= 1  -- trừ đi thay vì reset về 0 để tránh lệch chu kỳ
    end

    -- Màu RGB vẫn cập nhật mỗi frame → vẫn mượt
    local hue = (os.clock() % 3) / 3
    fpsLabel.TextColor3 = Color3.fromHSV(hue, 1, 1)
end)
