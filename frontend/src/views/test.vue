<template>
  <div class="test">
    <h1>{{ title }}</h1>
    <button @click="handleClick">Click me</button>
  </div>
</template>

<script>
  export default {
    name: 'TestComponent',
    data() {
      return {
        title: 'Hello World'
      }
    },
    methods: {
      handleClick() {
        console.log('clicked')
      }
    }
  }
</script>
