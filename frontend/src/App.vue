<script setup lang="ts">
</script>

<template>
  <div id="app">
    <header>
      <div class="header-inner">
        <div class="logo">Cover</div>
        <div class="tagline">Regulatory Engine</div>
      </div>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

html, body {
  overflow-x: hidden;
  width: 100%;
}

body {
  font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
  background: #fff;
  color: #1a1a1a;
  -webkit-font-smoothing: antialiased;
}

#app {
  min-height: 100vh;
}

header {
  border-bottom: 1px solid #eee;
  padding: 20px 40px;
  background: #fff;
}

.header-inner {
  max-width: 1400px;
  margin: 0 auto;
  display: flex;
  align-items: baseline;
  gap: 12px;
}

.logo {
  font-size: 22px;
  font-weight: 700;
  letter-spacing: -0.5px;
}

.tagline {
  font-size: 14px;
  color: #999;
  font-weight: 400;
}

main {
  max-width: 1400px;
  margin-left: auto;
  margin-right: auto;
  padding: 0 40px;
}
</style>
