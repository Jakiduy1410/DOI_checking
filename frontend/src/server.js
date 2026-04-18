
const express = require('express');
const path = require('path');

const app = express();
const PORT = 3000;

// tắt cache (tránh lỗi EJS)
app.set('view cache', false);

// view engine
app.set('view engine', 'ejs');
app.set('views', path.join(__dirname, 'views'));

// static file
app.use(express.static(path.join(__dirname, 'public')));

// route
app.get('/check', (req, res) => {
  res.render('index');
});

app.listen(PORT, () => {
  console.log(`Server chạy tại http://localhost:${PORT}/check`);
});