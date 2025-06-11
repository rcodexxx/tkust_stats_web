// src/config/theme.js

// 主題顏色定義
export const nintendoRed = '#E60012'
export const lightGreyText = '#888888'
export const bodyBgColor = '#F5F5F5'

// Naive UI 主題覆蓋配置
export const themeOverrides = {
  common: {
    primaryColor: nintendoRed,
    primaryColorHover: '#CC0010',
    primaryColorPressed: '#B3000E',
    primaryColorSuppl: nintendoRed,
    bodyColor: bodyBgColor,
    textColorBase: '#333333',
    fontSize: '14px'
  },
  Button: {
    textColorPrimary: '#FFFFFF'
  },
  Menu: {
    itemTextColorHorizontal: lightGreyText,
    itemIconColorHorizontal: lightGreyText,
    itemTextColorHoverHorizontal: nintendoRed,
    itemIconColorHoverHorizontal: nintendoRed,
    itemTextColorActiveHorizontal: nintendoRed,
    itemIconColorActiveHorizontal: nintendoRed,
    // 針對垂直 (Drawer) 選單的樣式
    itemTextColorVertical: '#555555',
    itemIconColorVertical: '#555555',
    itemTextColorHoverVertical: nintendoRed,
    itemIconColorHoverVertical: nintendoRed,
    itemTextColorActiveVertical: nintendoRed,
    itemIconColorActiveVertical: nintendoRed,
    itemColorActive: 'rgba(230, 0, 18, 0.1)' // 垂直選單選中項背景色
  },
  Layout: {},
  Drawer: {
    titleTextColor: nintendoRed,
    titleFontSize: '1.2rem'
  },
  Dropdown: {
    optionTextColor: '#333333'
  }
}
