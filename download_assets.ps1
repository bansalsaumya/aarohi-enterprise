$base = "https://aarohifoamlamination.com/assets/"
$outDir = "C:\Users\saumya bansal\OneDrive\Desktop\aarohi\assets"
$assets = @(
    "About-p3DhkPJ7.js","About-BN_Pzr7i.css",
    "Products-CfrS79FS.js","Products-BPNgfQwH.css",
    "ProductDetail-N5gLPRw4.js","InquiryForm-s-HrEETB.js","InquiryForm-BfwTN9Hb.css","ProductDetail-eDgJFwxK.css",
    "Blog-B3-lxI8M.js","blogsData-Dy76j_tF.js","Blog-CA9QcUvN.css",
    "BlogPostDetail-HSbS8sF7.js","BlogPostDetail-Vjs-dq03.css",
    "Contact-Dw6Npzuk.js","Contact-Cs5PQP4C.css",
    "AdminLogin-Bgm1y3hp.js","admin-C2ep2ydV.css",
    "AdminDashboard-DTtjzg3E.js","RequireAuth-De_yhTgJ.js"
)
foreach ($a in $assets) {
    Write-Host "Downloading $a"
    Invoke-WebRequest -Uri ($base + $a) -OutFile (Join-Path $outDir $a) -ErrorAction SilentlyContinue
}

# Download static assets from root
$rootAssets = @("web.logo.jpeg","logo_main.webp","logo_main.jpg","factory_2.webp","factory_quality.webp","factory_3.webp","video_main.mp4","aarohi_catalog.pdf")
foreach ($a in $rootAssets) {
    Write-Host "Downloading root: $a"
    Invoke-WebRequest -Uri ("https://aarohifoamlamination.com/" + $a) -OutFile (Join-Path "C:\Users\saumya bansal\OneDrive\Desktop\aarohi" $a) -ErrorAction SilentlyContinue
}

Write-Host "All downloads complete!"
