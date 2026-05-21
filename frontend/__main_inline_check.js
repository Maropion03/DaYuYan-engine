
  tailwind.config = {
    theme: {
      extend: {
        fontFamily: {
          sans: ['HarmonyOS Sans SC','HarmonyOS Sans','Source Han Sans SC','Source Han Sans CN','Noto Sans SC','PingFang SC','Microsoft YaHei','system-ui','sans-serif'],
          mono: ['JetBrains Mono','ui-monospace','SFMono-Regular','monospace'],
        },
        colors: {
          bg0:'#08090A', bg1:'#0E1013', bg2:'#14171B', bg3:'#1B1F25',
          line1:'rgba(255,255,255,.06)', line2:'rgba(255,255,255,.10)', line3:'rgba(255,255,255,.16)',
          t1:'#ECEDEE', t2:'#9BA1A6', t3:'#62676D',
          ba:'#FF7A18', bb:'#FF2D87',
          ok:'#10B981', warn:'#FACC15', danger:'#DC2626',
        },
        borderRadius: { '10':'10px' },
      },
    },
  };

