<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <meta http-equiv="X-UA-Compatible" content="ie=edge">
  <meta name="Description" content="Podcast 搜尋" />
  <title>Podcast 搜尋</title>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/twitter-bootstrap/4.6.0/css/bootstrap.min.css">
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/5.15.4/css/all.min.css">
  <script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js"></script>
  <style>
    body {
      font-family: Arial, sans-serif;
      margin: 20px;
    }
    h1 {
      text-align: center;
      margin-bottom: 30px;
    }
    .search-form, .category-btns {
      text-align: center;
      margin-bottom: 20px;
    }
    .btn {
      margin: 5px;
    }
    /* 新增用於 div 版式的樣式 */
    .podcast-table {
      margin-top: 20px;
      width: 100%;
    }
    .podcast-header {
      font-weight: bold;
      background-color: #f8f9fa;
      padding: 10px;
    }
    .podcast-row {
      display: flex;
      padding: 10px;
      border-bottom: 1px solid #dee2e6;
    }
    .podcast-cell {
      flex: 1;
      padding: 5px;
    }
    #error-message {
      color: red;
      text-align: center;
      font-weight: bold;
      margin-top: 20px;
    }
  </style>
</head>
<body>
  <h1>Podcast 搜尋</h1>
  <div class="container">
    <div class="row text-center">
      <div class="search-form col-12">
        <input type="text" id="searchInput" class="form-control" placeholder="輸入節目名稱" required>
        <button class="btn btn-primary" onclick="fetchPodcasts()">搜尋</button>
      </div>

      <!-- 按鈕來隱藏 "無資料" 列 -->
      <div class="hide-btn col-3 text-center">
        <button onclick="hideNoDataRows()">隱藏 "無資料" 的節目</button>
      </div>

      <!-- 動態排序按鈕 -->
      <div class="sort-btn col-3 text-center">
        <button onclick="sortTableByCategory()">按類別排序</button>
      </div>
    </div>

    <!-- 類別按鈕 -->
    <div class="col-12 text-center category-btns">
      <h4>選擇類別</h4>
      <div id="categoryButtons"></div>
    </div>

    <p id="error-message"></p>
    <!-- 使用 div 取代 table -->
    <div id="podcastTable" class="podcast-table">
      <!-- 表頭 -->
      <div class="podcast-header d-flex">
        <div class="podcast-cell text-center col-2">類別</div>
        <div class="podcast-cell text-center col-2">資料日期</div>
        <div class="podcast-cell text-center col-2">排行榜</div>
        <div class="podcast-cell text-center col-3">節目名稱</div>
        <div class="podcast-cell text-center col-3">主持人</div>
      </div>
      <!-- 資料列區塊 -->
      <div class="podcast-body"></div>
    </div>
  </div>

  <script>
    const supabaseUrl = 'https://xfnxyruqxvkbtophggyo.supabase.co';
    const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Inhmbnh5cnVxeHZrYnRvcGhnZ3lvIiwicm9sZSI6ImFub24iLCJpYXQiOjE3Mzg5ODgxMjMsImV4cCI6MjA1NDU2NDEyM30.BUmM4OTl9kbCBraAhNPSVvHY1pGSfsM-ZILkglbhsds';
    const supabaseClient = supabase.createClient(supabaseUrl, supabaseAnonKey);
    let currentCategory = null;

    document.addEventListener("DOMContentLoaded", function() {
      const categories = ['熱門', '社會與文化', '新聞', '教育', '商業', '健康與瘦身', '藝術', '音樂', '宗教與精神生活', '運動', '科學', '歷史', '犯罪紀實', '科技', '兒童與家庭', '電視與電影', '休閒', '小說', '政府'];
      const categoryButtonsContainer = document.getElementById("categoryButtons");
      
      if (categoryButtonsContainer) {
        categories.forEach(category => {
          const button = document.createElement("button");
          button.className = "btn btn-light m-2";
          button.innerText = category;
          button.onclick = () => fetchCategory(category);
          categoryButtonsContainer.appendChild(button);
        });
      }
    });

    // 按下搜尋按鈕後
    async function fetchPodcasts() {
      const body = document.querySelector("#podcastTable .podcast-body");
      body.innerHTML = "";
      currentCategory = null; // 清空當前類別
      try {
        const searchTerm = document.getElementById("searchInput").value.trim();
        let query = supabaseClient
          .from('podcasts')
          .select('*')
          .limit(200);
        
        // 如果有輸入搜尋關鍵字
        if (searchTerm) {
          query = query.ilike('title', `%${searchTerm}%`);
        }

        // 取得資料
        const { data, error } = await query;
        if (error) throw error;
        if (!data || data.length === 0) {
          document.getElementById("error-message").textContent = "沒有找到符合條件的 Podcast 資料。";
          return;
        }
        document.getElementById("error-message").textContent = "";

        // 依日期(降冪)，同日期則依 rank(升冪) 排列
        data.sort((a, b) => {
          if (a.date < b.date) return 1;
          if (a.date > b.date) return -1;
          return a.rank - b.rank;
        });

        data.forEach(podcast => {
          const row = document.createElement("div");
          row.className = "podcast-row d-flex";
          row.innerHTML = `
            <div class="podcast-cell text-center col-2">${podcast.category || '無資料'}</div>
            <div class="podcast-cell text-center col-2">${podcast.date || '無資料'}</div>
            <div class="podcast-cell text-center col-2">${podcast.rank || '無資料'}</div>
            <div class="podcast-cell text-center col-3">${podcast.title || '無資料'}</div>
            <div class="podcast-cell text-center col-3">${podcast.host || '無資料'}</div>
          `;
          body.appendChild(row);
        });
      } catch (err) {
        console.error("讀取 Podcast 錯誤：", err);
        document.getElementById("error-message").textContent = "讀取 Podcast 時發生錯誤，請檢查控制台。";
      }
    }

    // 點擊類別
    async function fetchCategory(category) {
      const body = document.querySelector("#podcastTable .podcast-body");
      body.innerHTML = "";
      currentCategory = category;
      try {
        // 先取得該類別所有資料
        const { data, error } = await supabaseClient
          .from('podcasts')
          .select('*')
          .eq('category', category);

        if (error) throw error;
        if (!data || data.length === 0) {
          document.getElementById("error-message").textContent = `沒有找到 ${category} 類別的 Podcast 資料。`;
          return;
        }
        document.getElementById("error-message").textContent = "";

        // 找出最新日期
        let maxDate = '';
        data.forEach(podcast => {
          if (podcast.date && podcast.date > maxDate) {
            maxDate = podcast.date;
          }
        });

        // 過濾出只包含最新日期的資料
        const latestData = data.filter(podcast => podcast.date === maxDate);

        // 依 rank(升冪) 排列
        latestData.sort((a, b) => a.rank - b.rank);

        latestData.forEach(podcast => {
          const row = document.createElement("div");
          row.className = "podcast-row d-flex";
          row.innerHTML = `
            <div class="podcast-cell text-center col-2">${podcast.category || '無資料'}</div>
            <div class="podcast-cell text-center col-2">${podcast.date || '無資料'}</div>
            <div class="podcast-cell text-center col-2">${podcast.rank || '無資料'}</div>
            <div class="podcast-cell text-center col-3">${podcast.title || '無資料'}</div>
            <div class="podcast-cell text-center col-3">${podcast.host || '無資料'}</div>
          `;
          body.appendChild(row);
        });
      } catch (err) {
        console.error(`讀取 ${category} Podcast 錯誤：`, err);
        document.getElementById("error-message").textContent = `讀取 ${category} Podcast 時發生錯誤，請檢查控制台。`;
      }
    }
  </script>

  <!-- JavaScript 用來隱藏 "無資料" 的行 和 按類別排序 -->
  <script>
    function hideNoDataRows() {
      const rows = document.querySelectorAll('#podcastTable .podcast-row');
      rows.forEach(row => {
        const cells = row.querySelectorAll('.podcast-cell');
        let hideRow = false;
        cells.forEach(cell => {
          if (cell.textContent === '無資料') {
            hideRow = true;
          }
        });
        if (hideRow) {
          row.style.display = 'none';
        }
      });
    }

    // 按類別和最新排名排序表格資料
    function sortTableByCategory() {
      const container = document.getElementById('podcastTable');
      const rows = Array.from(container.querySelectorAll('.podcast-body .podcast-row'));

      rows.sort((a, b) => {
        const cellsA = a.querySelectorAll('.podcast-cell');
        const cellsB = b.querySelectorAll('.podcast-cell');

        // 類別: 第 0 欄
        const categoryA = cellsA[0].innerText.toLowerCase();
        const categoryB = cellsB[0].innerText.toLowerCase();

        if (categoryA < categoryB) return -1;
        if (categoryA > categoryB) return 1;

        // 排名: 第 2 欄
        const rankingA = parseInt(cellsA[2].innerText) || 0;
        const rankingB = parseInt(cellsB[2].innerText) || 0;

        return rankingA - rankingB;
      });

      const body = container.querySelector('.podcast-body');
      rows.forEach(row => body.appendChild(row));
    }
  </script>
</body>
</html>
