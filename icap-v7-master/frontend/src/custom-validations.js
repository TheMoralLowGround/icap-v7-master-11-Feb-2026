/**
 * Organization: AIDocbuilder Inc.
 * File: custom-validation.js
 * Version: 6.0
 *
 * Authors:
 *   - Initial implementation: Vinay
 *
 * Last Updated By: Vinay
 * Last Updated At: 2023-11-01
 *
 * Description:
 *   This file contains custom validation rules for the Vee-Validate library,
 *   tailored to the application's specific requirements. These rules ensure
 *   input validation consistency and enhance user experience by providing
 *   meaningful error messages.
 *
 * Dependencies:
 *   - vee-validate
 *
 * Main Features:
 *   - Validation for text selection from images.
 *   - Anchor shape validation for specific field requirements.
 *   - Custom "required" rule allowing spaces.
 *   - Ensures at least one valid anchor shape is selected.
 *
 * Core Components:
 *   - `selectTextFromImage`
 *   - `validAnchorShape`
 *   - `requireAtleastOneAnchorShape`
 *   - `required-allow-space`
 *
 * Notes:
 *   - The rules are designed to be flexible and reusable across the application.
 *   - Parameters such as `selectionStatus` and `propertyName` allow dynamic validation logic.
 *   - Handles edge cases like missing or incomplete data to prevent validation failures.
 */

import { extend } from 'vee-validate'

extend('selectTextFromImage', {
  message: 'Please select text from image',
  params: ['selectionStatus'],
  validate: (value, { selectionStatus }) => {
    if (!value) {
      return true
    }

    if (selectionStatus === 'true') {
      return true
    }

    return false
  },
})

extend('validAnchorShape', {
  message: 'Please select valid anchor shape',
  validate: value => {
    if (value.text && !value.pos) {
      return false
    }
    return true
  },
})

extend('requireAtleastOneAnchorShape', {
  message: 'Please select atleast one anchor shape',
  params: ['propertyName'],
  validate: (value, { propertyName }) => {
    let isValid = false

    let anchors
    if (propertyName === 'root') {
      anchors = value
    } else {
      anchors = value[propertyName]
    }

    const anchorPositions = ['top', 'bottom', 'left', 'right']
    for (let index = 0; index < anchorPositions.length; index += 1) {
      const anchorPosition = anchorPositions[index]
      if (anchors[anchorPosition]?.pos) {
        isValid = true
        break
      }
    }

    return isValid
  },
})

extend('required-allow-space', {
  validate(value) {
    return {
      required: true,
      valid: ['', null, undefined].indexOf(value) === -1,
    }
  },
  message: 'The {_field_} field is required',
  computesRequired: true,
})
