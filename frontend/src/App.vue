<script setup lang="ts">
</script>

<template>
  <div id="app">
    <header>
      <h1>Cover Regulatory Engine</h1>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
  background: #f5f5f5;
  color: #1a1a1a;
}

#app {
  min-height: 100vh;
}

header {
  background: #fff;
  border-bottom: 1px solid #e0e0e0;
  padding: 16px 24px;
}

header h1 {
  font-size: 20px;
  font-weight: 600;
}

main {
  max-width: 1400px;
  margin: 0 auto;
  padding: 24px;
}
</style>
