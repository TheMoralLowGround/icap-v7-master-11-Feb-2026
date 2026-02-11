<template>
  <!-- Display the scroll-to-top button only when scrollTop is greater than 10 -->
  <div
    v-if="scrollTop > 10"
    class="scroll-to-top"
  >
    <!-- Feather icon that represents an up arrow for scrolling up -->
    <feather-icon
      icon="ChevronsUpIcon"
      size="30"
      class="cursor-pointer mx-1"
      :style="{
        'opacity': scrollToTopIconHover ? 1 : 0.5
      }"
      @mouseover="scrollToTopIconHover = true"
      @mouseleave="scrollToTopIconHover = false"
      @click="onScrollToTop"
    />
  </div>
</template>

<script>
import bus from '@/bus' // Import the event bus for global event handling

export default {
  data() {
    return {
      scrollTop: 0, // Tracks the current scroll position
      scrollToTopIconHover: false, // Tracks the hover state of the scroll-to-top icon
    }
  },
  created() {
    // Listen for the 'dataView/onScroll' event to update the scroll position
    bus.$on('dataView/onScroll', this.onScroll)
  },
  destroyed() {
    // Remove the event listener when the component is destroyed to avoid memory leaks
    bus.$off('dataView/onScroll', this.onScroll)
  },
  methods: {
    // Method to update the scroll position when the scroll event is triggered
    onScroll(e) {
      this.scrollTop = e.currentTarget.scrollTop
    },

    // Method to scroll the page to the top when the scroll-to-top icon is clicked
    onScrollToTop() {
      // Select the content wrapper element to scroll to the top
      const querySelector = document.querySelector('.definitions-content-wrapper')

      // Scroll to the top instantly with no animation
      querySelector.scroll({
        top: 0,
        behavior: 'instant',
      })

      // Reset the hover state of the icon after clicking
      this.scrollToTopIconHover = false
    },
  },
}
</script>

<style scoped>
/* Position the scroll-to-top button fixed at the bottom-right of the screen */
.scroll-to-top {
  position: fixed;
  bottom: 3rem;
  right: 2rem;
}
</style>
