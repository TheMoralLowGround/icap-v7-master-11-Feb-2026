<template>
  <div
    class="custom-avatar"
    :class="[
      `avatar-${size}`,
      variant ? `avatar-${variant}` : '',
      rounded ? 'rounded-circle' : ''
    ]"
    :style="avatarStyle"
  >
    <span
      class="avatar-text"
      :style="textStyle"
    >
      {{ displayText }}
    </span>
  </div>
</template>

<script>
export default {
  name: 'CustomAvatar',
  props: {
    text: {
      type: String,
      default: '',
    },
    size: {
      type: [String, Number],
      default: '40',
    },
    variant: {
      type: String,
      default: 'light-primary',
    },
    textColor: {
      type: String,
      default: null,
    },
    backgroundColor: {
      type: String,
      default: null,
    },
    rounded: {
      type: Boolean,
      default: true,
    },
    fontSize: {
      type: [String, Number],
      default: null,
    },
  },
  computed: {
    displayText() {
      return this.text || ''
    },
    sizeValue() {
      return typeof this.size === 'string' ? parseInt(this.size, 10) : this.size
    },
    avatarStyle() {
      const styles = {
        width: `${this.sizeValue}px`,
        height: `${this.sizeValue}px`,
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        fontWeight: '600',
        userSelect: 'none',
      }

      // Custom background color overrides variant
      if (this.backgroundColor) {
        styles.backgroundColor = this.backgroundColor
      }

      return styles
    },
    textStyle() {
      const styles = {}

      // Custom text color
      if (this.textColor) {
        styles.color = this.textColor
      }

      // Calculate font size based on avatar size
      const calculatedFontSize = this.fontSize || Math.floor(this.sizeValue * 0.4)
      styles.fontSize = typeof calculatedFontSize === 'number'
        ? `${calculatedFontSize}px`
        : calculatedFontSize

      return styles
    },
  },
}
</script>

<style scoped>
.custom-avatar {
  position: relative;
  border-radius: 0.375rem; /* Default border radius */
}

.custom-avatar.rounded-circle {
  border-radius: 50% !important;
}

.avatar-text {
  line-height: 1;
  text-transform: uppercase;
  font-family: inherit;
}

/* Size variations */
.avatar-sm, .avatar-small {
  --avatar-size: 32px;
}

.avatar-lg, .avatar-large {
  --avatar-size: 56px;
}

.avatar-xl, .avatar-extra-large {
  --avatar-size: 72px;
}

/* Variant styles - Bootstrap-like colors */
.avatar-primary {
  background-color: #0d6efd;
  color: #ffffff;
}

.avatar-light-primary {
  background-color: #e7f1ff;
  color: #0d6efd;
}

.avatar-secondary {
  background-color: #6c757d;
  color: #ffffff;
}

.avatar-light-secondary {
  background-color: #f8f9fa;
  color: #6c757d;
}

.avatar-success {
  background-color: #198754;
  color: #ffffff;
}

.avatar-light-success {
  background-color: #d1e7dd;
  color: #198754;
}

.avatar-danger {
  background-color: #dc3545;
  color: #ffffff;
}

.avatar-light-danger {
  background-color: #f8d7da;
  color: #dc3545;
}

.avatar-warning {
  background-color: #ffc107;
  color: #000000;
}

.avatar-light-warning {
  background-color: #fff3cd;
  color: #664d03;
}

.avatar-info {
  background-color: #0dcaf0;
  color: #000000;
}

.avatar-light-info {
  background-color: #d1ecf1;
  color: #055160;
}

.avatar-dark {
  background-color: #212529;
  color: #ffffff;
}

.avatar-light {
  background-color: #f8f9fa;
  color: #212529;
}

/* Theme-aware variants (works with Vuexy) */
[data-theme="dark"] .avatar-light-primary {
  background-color: rgba(13, 110, 253, 0.16);
  color: #5a8dee;
}

[data-theme="dark"] .avatar-light-secondary {
  background-color: rgba(108, 117, 125, 0.16);
  color: #a8b1bb;
}

[data-theme="dark"] .avatar-light-success {
  background-color: rgba(25, 135, 84, 0.16);
  color: #28c76f;
}

[data-theme="dark"] .avatar-light-danger {
  background-color: rgba(220, 53, 69, 0.16);
  color: #ea5455;
}

[data-theme="dark"] .avatar-light-warning {
  background-color: rgba(255, 193, 7, 0.16);
  color: #ff9f43;
}

[data-theme="dark"] .avatar-light-info {
  background-color: rgba(13, 202, 240, 0.16);
  color: #00cfe8;
}
</style>
