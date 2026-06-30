/* ===================== 虚拟人形象库 =====================
 * 提供多款预设形象 + 可自定义形象(参数化机器人)。
 * 每个 SVG 都使用统一的动画钩子 class:
 *   avatar-float / avatar-head / avatar-eye / avatar-mouth
 *   avatar-shadow / avatar-think(.think-dot td1/td2/td3)
 * 这样所有形象都能复用 待机/思考/说话 状态动画。
 * ===================================================== */
(function (global) {
  "use strict";

  function shadow(color) {
    return '<ellipse class="avatar-shadow" cx="100" cy="186" rx="48" ry="8" fill="' + color + '"/>';
  }
  function think(color) {
    return (
      '<g class="avatar-think">' +
      '<circle class="think-dot td1" cx="150" cy="48" r="5" fill="' + color + '"/>' +
      '<circle class="think-dot td2" cx="162" cy="38" r="7" fill="' + color + '"/>' +
      '<circle class="think-dot td3" cx="176" cy="26" r="9" fill="' + color + '"/>' +
      "</g>"
    );
  }
  function wrap(inner) {
    return '<svg viewBox="0 0 200 200" xmlns="http://www.w3.org/2000/svg">' + inner + "</svg>";
  }

  /* -------- 预设形象 -------- */
  var advisor = wrap(
    '<defs>' +
      '<linearGradient id="adSuit" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#27488f"/><stop offset="100%" stop-color="#16264f"/></linearGradient>' +
      '<radialGradient id="adSkin" cx="50%" cy="42%" r="62%"><stop offset="0%" stop-color="#ffe8d2"/><stop offset="100%" stop-color="#f3c098"/></radialGradient>' +
      '<linearGradient id="adHair" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#4a3424"/><stop offset="100%" stop-color="#2c1e13"/></linearGradient>' +
      '<radialGradient id="adEye" cx="38%" cy="32%" r="72%"><stop offset="0%" stop-color="#6b5743"/><stop offset="100%" stop-color="#1c130b"/></radialGradient>' +
    '</defs>' +
    shadow("#94a3b8") + think("#93c5fd") +
    '<g class="avatar-float">' +
      '<path d="M48 190 Q46 138 78 128 Q100 122 122 128 Q154 138 152 190 Z" fill="url(#adSuit)"/>' +
      '<path d="M84 128 Q100 124 116 128 L100 150 Z" fill="#f8fafc"/>' +
      '<path d="M88 128 L100 150 L84 164 L80 134 Z" fill="#1a3266"/>' +
      '<path d="M112 128 L100 150 L116 164 L120 134 Z" fill="#1a3266"/>' +
      '<path d="M96 130 L100 148 L104 130 L100 126 Z" fill="#3b82f6"/>' +
      '<path d="M100 148 L96 168 L100 174 L104 168 Z" fill="#2563eb"/>' +
      '<rect x="92" y="112" width="16" height="20" rx="7" fill="#f0b78a"/>' +
      '<g class="avatar-head">' +
        '<ellipse cx="100" cy="86" rx="35" ry="38" fill="url(#adSkin)"/>' +
        '<ellipse cx="65" cy="90" rx="6" ry="9" fill="#f0b78a"/>' +
        '<ellipse cx="135" cy="90" rx="6" ry="9" fill="#f0b78a"/>' +
        '<path d="M64 80 Q60 42 100 42 Q140 42 136 80 Q132 58 100 56 Q68 58 64 80 Z" fill="url(#adHair)"/>' +
        '<path d="M64 80 Q66 62 80 54 Q70 70 70 86 Z" fill="#5a4230" opacity="0.6"/>' +
        '<path d="M76 70 Q86 65 96 69" stroke="#3a2818" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
        '<path d="M104 69 Q114 65 124 70" stroke="#3a2818" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
        '<g class="avatar-eye">' +
          '<circle cx="85" cy="86" r="7" fill="url(#adEye)"/>' +
          '<circle cx="115" cy="86" r="7" fill="url(#adEye)"/>' +
          '<circle cx="87.5" cy="83.5" r="2.4" fill="#fff"/>' +
          '<circle cx="117.5" cy="83.5" r="2.4" fill="#fff"/>' +
          '<circle cx="83" cy="88.5" r="1.1" fill="#fff" opacity="0.6"/>' +
          '<circle cx="113" cy="88.5" r="1.1" fill="#fff" opacity="0.6"/>' +
        '</g>' +
        '<path d="M97 95 Q100 98 103 95" stroke="#d99a6c" stroke-width="1.6" fill="none" stroke-linecap="round"/>' +
        '<circle cx="76" cy="98" r="5.5" fill="#fb7185" opacity="0.35"/>' +
        '<circle cx="124" cy="98" r="5.5" fill="#fb7185" opacity="0.35"/>' +
        '<path class="avatar-mouth" d="M91 106 Q100 113 109 106 Q100 109 91 106 Z" fill="#b56a58"/>' +
      "</g>" +
    "</g>"
  );

  var mascot = wrap(
    '<defs>' +
      '<radialGradient id="msBody" cx="50%" cy="36%" r="68%"><stop offset="0%" stop-color="#fff1c2"/><stop offset="60%" stop-color="#fcd34d"/><stop offset="100%" stop-color="#f59e0b"/></radialGradient>' +
      '<radialGradient id="msEye" cx="40%" cy="32%" r="70%"><stop offset="0%" stop-color="#4b5563"/><stop offset="100%" stop-color="#111827"/></radialGradient>' +
      '<linearGradient id="msBeak" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fb923c"/><stop offset="100%" stop-color="#ea7317"/></linearGradient>' +
    '</defs>' +
    shadow("#d97706") + think("#fcd34d") +
    '<g class="avatar-float"><g class="avatar-head">' +
      '<path d="M100 48 Q95 34 88 30 Q96 32 100 42 Q104 32 112 30 Q105 34 100 48 Z" fill="#22c55e"/>' +
      '<ellipse cx="100" cy="112" rx="60" ry="58" fill="url(#msBody)"/>' +
      '<ellipse cx="100" cy="120" rx="38" ry="40" fill="#fffdf2" opacity="0.55"/>' +
      '<ellipse cx="50" cy="118" rx="11" ry="15" fill="#f59e0b"/>' +
      '<ellipse cx="150" cy="118" rx="11" ry="15" fill="#f59e0b"/>' +
      '<circle cx="64" cy="124" r="9" fill="#fb7185" opacity="0.5"/>' +
      '<circle cx="136" cy="124" r="9" fill="#fb7185" opacity="0.5"/>' +
      '<circle class="avatar-twinkle" cx="150" cy="92" r="15" fill="#fbbf24" stroke="#d97706" stroke-width="2.5"/>' +
      '<text x="150" y="98" font-size="16" text-anchor="middle" fill="#b45309" font-weight="bold">¥</text>' +
      '<g class="avatar-eye">' +
        '<circle cx="82" cy="100" r="10" fill="url(#msEye)"/>' +
        '<circle cx="118" cy="100" r="10" fill="url(#msEye)"/>' +
        '<circle cx="85" cy="96" r="3.4" fill="#fff"/>' +
        '<circle cx="121" cy="96" r="3.4" fill="#fff"/>' +
        '<circle cx="79" cy="103" r="1.5" fill="#fff" opacity="0.6"/>' +
        '<circle cx="115" cy="103" r="1.5" fill="#fff" opacity="0.6"/>' +
      '</g>' +
      '<path class="avatar-mouth" d="M91 120 Q100 130 109 120 Q100 124 91 120 Z" fill="url(#msBeak)"/>' +
    "</g></g>"
  );

  var robot = wrap(
    '<defs>' +
      '<linearGradient id="rbHead" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#cfe3f5"/></linearGradient>' +
      '<radialGradient id="rbVisor" cx="50%" cy="36%" r="72%"><stop offset="0%" stop-color="#15546b"/><stop offset="100%" stop-color="#062b38"/></radialGradient>' +
      '<linearGradient id="rbBody" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#22b8d4"/><stop offset="100%" stop-color="#155e75"/></linearGradient>' +
      '<radialGradient id="rbEye" cx="50%" cy="40%" r="70%"><stop offset="0%" stop-color="#ecfeff"/><stop offset="55%" stop-color="#67e8f9"/><stop offset="100%" stop-color="#06b6d4"/></radialGradient>' +
    '</defs>' +
    shadow("#0e7490") + think("#67e8f9") +
    '<g class="avatar-float">' +
      '<path d="M62 186 Q60 138 100 134 Q140 138 138 186 Z" fill="url(#rbBody)"/>' +
      '<rect x="76" y="150" width="48" height="20" rx="10" fill="#0a3a48" opacity="0.6"/>' +
      '<circle class="avatar-twinkle" cx="100" cy="160" r="6" fill="#67e8f9"/>' +
      '<rect x="92" y="120" width="16" height="18" rx="6" fill="#bcd7e6"/>' +
      '<g class="avatar-head">' +
        '<rect x="54" y="48" width="92" height="80" rx="34" fill="url(#rbHead)" stroke="#bae6fd" stroke-width="2"/>' +
        '<ellipse cx="80" cy="66" rx="16" ry="9" fill="#ffffff" opacity="0.6"/>' +
        '<line x1="100" y1="48" x2="100" y2="32" stroke="#94a3b8" stroke-width="3"/>' +
        '<circle class="avatar-twinkle" cx="100" cy="28" r="5.5" fill="#22d3ee"/>' +
        '<rect x="64" y="66" width="72" height="48" rx="22" fill="url(#rbVisor)"/>' +
        '<rect x="64" y="66" width="72" height="20" rx="10" fill="#2dd4bf" opacity="0.18"/>' +
        '<g class="avatar-eye">' +
          '<circle cx="84" cy="90" r="9" fill="url(#rbEye)"/>' +
          '<circle cx="116" cy="90" r="9" fill="url(#rbEye)"/>' +
          '<circle cx="86.5" cy="87" r="2.6" fill="#fff"/>' +
          '<circle cx="118.5" cy="87" r="2.6" fill="#fff"/>' +
        '</g>' +
        '<rect class="avatar-mouth" x="90" y="104" width="20" height="6" rx="3" fill="#7df0fb"/>' +
        '<rect x="48" y="78" width="9" height="22" rx="4.5" fill="#67e8f9"/>' +
        '<rect x="143" y="78" width="9" height="22" rx="4.5" fill="#67e8f9"/>' +
      "</g>" +
    "</g>"
  );

  var westie = wrap(
    '<defs>' +
      '<radialGradient id="wdFur" cx="50%" cy="36%" r="72%"><stop offset="0%" stop-color="#ffffff"/><stop offset="68%" stop-color="#f6f7f9"/><stop offset="100%" stop-color="#e2e6ea"/></radialGradient>' +
      '<radialGradient id="wdHead" cx="50%" cy="40%" r="66%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#e6eaee"/></radialGradient>' +
      '<linearGradient id="wdEar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fbe3e8"/><stop offset="100%" stop-color="#f3c2cd"/></linearGradient>' +
      '<radialGradient id="wdEye" cx="38%" cy="32%" r="72%"><stop offset="0%" stop-color="#6b5340"/><stop offset="100%" stop-color="#1a120b"/></radialGradient>' +
    '</defs>' +
    shadow("#9ca3af") + think("#cbd5e1") +
    '<g class="avatar-float">' +
      '<path d="M56 190 Q50 150 64 138 Q82 126 100 126 Q118 126 136 138 Q150 150 144 190 Z" fill="url(#wdFur)"/>' +
      '<path d="M66 152 Q70 139 83 142 Q78 152 85 162 Q72 162 66 152 Z" fill="#ffffff" opacity="0.85"/>' +
      '<path d="M134 152 Q130 139 117 142 Q122 152 115 162 Q128 162 134 152 Z" fill="#ffffff" opacity="0.85"/>' +
      '<ellipse cx="80" cy="186" rx="12" ry="9" fill="#ffffff" stroke="#e0e4e8" stroke-width="1.5"/>' +
      '<ellipse cx="120" cy="186" rx="12" ry="9" fill="#ffffff" stroke="#e0e4e8" stroke-width="1.5"/>' +
      '<path d="M74 132 Q100 145 126 132 L124 141 Q100 152 76 141 Z" fill="#dc2626"/>' +
      '<circle cx="100" cy="147" r="5" fill="#fbbf24" stroke="#d97706" stroke-width="1"/>' +
      '<g class="avatar-head">' +
        '<path d="M62 64 Q50 28 74 38 Q88 46 90 72 Q74 60 62 64 Z" fill="url(#wdFur)"/>' +
        '<path d="M138 64 Q150 28 126 38 Q112 46 110 72 Q126 60 138 64 Z" fill="url(#wdFur)"/>' +
        '<path d="M68 56 Q63 40 75 45 Q81 53 81 65 Z" fill="url(#wdEar)" opacity="0.7"/>' +
        '<path d="M132 56 Q137 40 125 45 Q119 53 119 65 Z" fill="url(#wdEar)" opacity="0.7"/>' +
        '<path d="M58 92 Q54 50 100 50 Q146 50 142 92 Q142 105 133 113 Q140 121 129 125 Q123 133 113 128 Q107 135 100 133 Q93 135 87 128 Q77 133 71 125 Q60 121 67 113 Q58 105 58 92 Z" fill="url(#wdHead)"/>' +
        '<path d="M64 96 Q61 117 79 123 Q70 109 72 96 Z" fill="#ffffff"/>' +
        '<path d="M136 96 Q139 117 121 123 Q130 109 128 96 Z" fill="#ffffff"/>' +
        '<path d="M71 72 Q84 63 97 72 Q84 69 71 72 Z" fill="#ffffff"/>' +
        '<path d="M129 72 Q116 63 103 72 Q116 69 129 72 Z" fill="#ffffff"/>' +
        '<g class="avatar-eye">' +
          '<circle cx="83" cy="88" r="8" fill="url(#wdEye)"/>' +
          '<circle cx="117" cy="88" r="8" fill="url(#wdEye)"/>' +
          '<circle cx="86" cy="85" r="2.7" fill="#fff"/>' +
          '<circle cx="120" cy="85" r="2.7" fill="#fff"/>' +
          '<circle cx="80" cy="91" r="1.3" fill="#fff" opacity="0.65"/>' +
          '<circle cx="114" cy="91" r="1.3" fill="#fff" opacity="0.65"/>' +
        '</g>' +
        '<ellipse cx="100" cy="111" rx="22" ry="15" fill="#ffffff"/>' +
        '<path d="M100 98 Q109 98 107 105 Q104 110 100 111 Q96 110 93 105 Q91 98 100 98 Z" fill="#211a14"/>' +
        '<circle cx="97" cy="101" r="1.3" fill="#6b5e54" opacity="0.6"/>' +
        '<path d="M100 111 L100 116" stroke="#9a8478" stroke-width="1.6" stroke-linecap="round"/>' +
        '<path d="M100 116 Q92 122 86 118" stroke="#9a8478" stroke-width="1.6" fill="none" stroke-linecap="round"/>' +
        '<path d="M100 116 Q108 122 114 118" stroke="#9a8478" stroke-width="1.6" fill="none" stroke-linecap="round"/>' +
        '<ellipse class="avatar-mouth" cx="100" cy="119" rx="5.5" ry="3" fill="#c98a86"/>' +
      "</g>" +
    "</g>"
  );

  var cat = wrap(
    '<defs>' +
      '<radialGradient id="ctFur" cx="50%" cy="36%" r="72%"><stop offset="0%" stop-color="#e6a268"/><stop offset="100%" stop-color="#bd7d44"/></radialGradient>' +
      '<radialGradient id="ctHead" cx="50%" cy="40%" r="66%"><stop offset="0%" stop-color="#edb079"/><stop offset="100%" stop-color="#cd8c52"/></radialGradient>' +
      '<linearGradient id="ctEar" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f7b8c4"/><stop offset="100%" stop-color="#e98ba0"/></linearGradient>' +
      '<radialGradient id="ctEye" cx="42%" cy="30%" r="72%"><stop offset="0%" stop-color="#8a5a30"/><stop offset="52%" stop-color="#5a3818"/><stop offset="100%" stop-color="#2e1a0a"/></radialGradient>' +
    '</defs>' +
    shadow("#5b3a1a") + think("#d6b06a") +
    '<g class="avatar-float">' +
      '<path class="avatar-tail" d="M138 182 Q180 174 172 130 Q166 119 157 124 Q167 150 149 163 Q142 169 138 182 Z" fill="url(#ctFur)"/>' +
      '<path class="avatar-tail" d="M160 128 Q168 134 165 146" stroke="#9a6630" stroke-width="3" fill="none" stroke-linecap="round"/>' +
      '<path d="M62 190 Q58 142 100 134 Q142 142 138 190 Z" fill="url(#ctFur)"/>' +
      '<path d="M84 150 Q100 142 116 150 Q120 173 100 181 Q80 173 84 150 Z" fill="#f4d2a6" opacity="0.85"/>' +
      '<ellipse cx="84" cy="186" rx="11" ry="8" fill="#cf8b50"/>' +
      '<ellipse cx="116" cy="186" rx="11" ry="8" fill="#cf8b50"/>' +
      '<g class="avatar-head">' +
        '<path d="M60 66 L54 28 Q72 40 86 52 Z" fill="url(#ctHead)"/>' +
        '<path d="M140 66 L146 28 Q128 40 114 52 Z" fill="url(#ctHead)"/>' +
        '<path d="M66 60 L62 38 Q74 46 82 54 Z" fill="url(#ctEar)"/>' +
        '<path d="M134 60 L138 38 Q126 46 118 54 Z" fill="url(#ctEar)"/>' +
        '<ellipse cx="100" cy="92" rx="46" ry="43" fill="url(#ctHead)"/>' +
        '<path d="M100 50 L100 64" stroke="#9a6630" stroke-width="3" stroke-linecap="round"/>' +
        '<path d="M89 52 L86 64" stroke="#9a6630" stroke-width="2.5" stroke-linecap="round"/>' +
        '<path d="M111 52 L114 64" stroke="#9a6630" stroke-width="2.5" stroke-linecap="round"/>' +
        '<ellipse cx="100" cy="108" rx="26" ry="18" fill="#f4d2a6" opacity="0.9"/>' +
        '<g class="avatar-eye">' +
          '<ellipse cx="82" cy="90" rx="9" ry="11" fill="url(#ctEye)"/>' +
          '<ellipse cx="118" cy="90" rx="9" ry="11" fill="url(#ctEye)"/>' +
          '<ellipse cx="82" cy="91" rx="3.1" ry="7" fill="#1a0e04"/>' +
          '<ellipse cx="118" cy="91" rx="3.1" ry="7" fill="#1a0e04"/>' +
          '<circle cx="85" cy="85" r="2.6" fill="#fff"/>' +
          '<circle cx="121" cy="85" r="2.6" fill="#fff"/>' +
        '</g>' +
        '<path d="M100 102 l-5 4.5 h10 z" fill="#e98ba0"/>' +
        '<path d="M100 106 L100 110" stroke="#9a5a26" stroke-width="1.6" stroke-linecap="round"/>' +
        '<path d="M100 110 Q93 116 86 112" stroke="#9a6630" stroke-width="1.8" fill="none" stroke-linecap="round"/>' +
        '<path d="M100 110 Q107 116 114 112" stroke="#9a6630" stroke-width="1.8" fill="none" stroke-linecap="round"/>' +
        '<ellipse class="avatar-mouth" cx="100" cy="114" rx="5" ry="3" fill="#c2607a"/>' +
        '<path d="M52 100 Q66 99 74 102" stroke="#fff" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.85"/>' +
        '<path d="M52 108 Q66 108 74 108" stroke="#fff" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.85"/>' +
        '<path d="M148 100 Q134 99 126 102" stroke="#fff" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.85"/>' +
        '<path d="M148 108 Q134 108 126 108" stroke="#fff" stroke-width="1.5" fill="none" stroke-linecap="round" opacity="0.85"/>' +
      "</g>" +
    "</g>"
  );

  var lady = wrap(
    '<defs>' +
      '<linearGradient id="ldSuit" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#8b46f0"/><stop offset="100%" stop-color="#5b21b6"/></linearGradient>' +
      '<radialGradient id="ldSkin" cx="50%" cy="42%" r="62%"><stop offset="0%" stop-color="#ffe8d2"/><stop offset="100%" stop-color="#f3c098"/></radialGradient>' +
      '<linearGradient id="ldHair" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#5a3a24"/><stop offset="100%" stop-color="#33200f"/></linearGradient>' +
      '<radialGradient id="ldEye" cx="38%" cy="32%" r="72%"><stop offset="0%" stop-color="#7a5a44"/><stop offset="100%" stop-color="#241710"/></radialGradient>' +
    '</defs>' +
    shadow("#94a3b8") + think("#c4b5fd") +
    '<g class="avatar-float">' +
      '<path d="M50 190 Q48 136 80 128 Q100 122 120 128 Q152 136 150 190 Z" fill="url(#ldSuit)"/>' +
      '<path d="M86 128 Q100 124 114 128 L100 148 Z" fill="#f8fafc"/>' +
      '<rect x="92" y="112" width="16" height="20" rx="7" fill="#f0b78a"/>' +
      '<path d="M52 100 Q44 150 70 180 L88 138 Q62 124 64 92 Z" fill="url(#ldHair)"/>' +
      '<path d="M148 100 Q156 150 130 180 L112 138 Q138 124 136 92 Z" fill="url(#ldHair)"/>' +
      '<g class="avatar-head">' +
        '<ellipse cx="100" cy="88" rx="33" ry="37" fill="url(#ldSkin)"/>' +
        '<path d="M56 100 Q46 36 100 32 Q154 36 144 100 Q142 78 128 68 Q132 80 122 80 Q123 64 100 60 Q77 64 78 80 Q68 80 72 68 Q58 78 56 100 Z" fill="url(#ldHair)"/>' +
        '<path d="M58 72 Q53 104 64 126 Q73 122 74 104 Q70 90 76 78 Q66 78 62 72 Z" fill="url(#ldHair)"/>' +
        '<path d="M142 72 Q147 104 136 126 Q127 122 126 104 Q130 90 124 78 Q134 78 138 72 Z" fill="url(#ldHair)"/>' +
        '<path d="M62 98 Q60 62 82 54 Q70 74 72 98 Z" fill="#6a4528" opacity="0.5"/>' +
        '<path d="M138 98 Q140 64 120 56 Q132 74 130 98 Z" fill="#33200f" opacity="0.4"/>' +
        '<path d="M88 42 Q96 37 104 41" stroke="#fbbf24" stroke-width="2" fill="none" stroke-linecap="round"/>' +
        '<path d="M79 80 Q86 76 93 80" stroke="#4b2e1e" stroke-width="2" fill="none" stroke-linecap="round"/>' +
        '<path d="M107 80 Q114 76 121 80" stroke="#4b2e1e" stroke-width="2" fill="none" stroke-linecap="round"/>' +
        '<g class="avatar-eye">' +
          '<circle cx="86" cy="88" r="6.5" fill="url(#ldEye)"/>' +
          '<circle cx="114" cy="88" r="6.5" fill="url(#ldEye)"/>' +
          '<circle cx="88.3" cy="85.5" r="2.3" fill="#fff"/>' +
          '<circle cx="116.3" cy="85.5" r="2.3" fill="#fff"/>' +
        '</g>' +
        '<path d="M80 82 Q86 79 92 81" stroke="#3a2316" stroke-width="1.4" fill="none" stroke-linecap="round"/>' +
        '<path d="M108 81 Q114 79 120 82" stroke="#3a2316" stroke-width="1.4" fill="none" stroke-linecap="round"/>' +
        '<circle cx="75" cy="100" r="5.5" fill="#fb7185" opacity="0.4"/>' +
        '<circle cx="125" cy="100" r="5.5" fill="#fb7185" opacity="0.4"/>' +
        '<path class="avatar-mouth" d="M92 107 Q100 113 108 107 Q100 110 92 107 Z" fill="#e1466b"/>' +
      "</g>" +
    "</g>"
  );

  var panda = wrap(
    '<defs>' +
      '<radialGradient id="pdBody" cx="50%" cy="36%" r="64%"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#e7eaee"/></radialGradient>' +
      '<radialGradient id="pdEar" cx="50%" cy="40%" r="60%"><stop offset="0%" stop-color="#3a3f47"/><stop offset="100%" stop-color="#161a1f"/></radialGradient>' +
      '<radialGradient id="pdEye" cx="42%" cy="32%" r="70%"><stop offset="0%" stop-color="#4b5563"/><stop offset="100%" stop-color="#0d1117"/></radialGradient>' +
    '</defs>' +
    shadow("#6b7280") + think("#9ca3af") +
    '<g class="avatar-float"><g class="avatar-head">' +
      '<circle cx="68" cy="50" r="17" fill="url(#pdEar)"/>' +
      '<circle cx="132" cy="50" r="17" fill="url(#pdEar)"/>' +
      '<circle cx="68" cy="50" r="8" fill="#2b3036"/>' +
      '<circle cx="132" cy="50" r="8" fill="#2b3036"/>' +
      '<circle cx="100" cy="92" r="50" fill="url(#pdBody)"/>' +
      '<ellipse cx="78" cy="74" rx="14" ry="10" fill="#fff" opacity="0.5"/>' +
      '<ellipse cx="80" cy="88" rx="13" ry="17" fill="url(#pdEye)" transform="rotate(-16 80 88)"/>' +
      '<ellipse cx="120" cy="88" rx="13" ry="17" fill="url(#pdEye)" transform="rotate(16 120 88)"/>' +
      '<g class="avatar-eye">' +
        '<circle cx="82" cy="88" r="6" fill="#fff"/>' +
        '<circle cx="118" cy="88" r="6" fill="#fff"/>' +
        '<circle cx="82" cy="89" r="3.4" fill="#1b1f24"/>' +
        '<circle cx="118" cy="89" r="3.4" fill="#1b1f24"/>' +
        '<circle cx="84" cy="86" r="1.4" fill="#fff"/>' +
        '<circle cx="120" cy="86" r="1.4" fill="#fff"/>' +
      '</g>' +
      '<circle cx="68" cy="104" r="7" fill="#fb7185" opacity="0.4"/>' +
      '<circle cx="132" cy="104" r="7" fill="#fb7185" opacity="0.4"/>' +
      '<path d="M100 100 l-5 4 h10 z" fill="#1f2937"/>' +
      '<path d="M100 104 L100 108" stroke="#374151" stroke-width="1.6" stroke-linecap="round"/>' +
      '<path class="avatar-mouth" d="M91 109 Q100 117 109 109 Q100 113 91 109 Z" fill="#6b7280"/>' +
      '<circle class="avatar-twinkle" cx="150" cy="106" r="13" fill="#fbbf24" stroke="#d97706" stroke-width="2"/>' +
      '<text x="150" y="112" font-size="14" text-anchor="middle" fill="#b45309" font-weight="bold">¥</text>' +
    "</g></g>"
  );

  var fortune = wrap(
    '<defs>' +
      '<linearGradient id="ftRobe" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#f04848"/><stop offset="100%" stop-color="#991b1b"/></linearGradient>' +
      '<radialGradient id="ftSkin" cx="50%" cy="42%" r="62%"><stop offset="0%" stop-color="#ffe8d2"/><stop offset="100%" stop-color="#f3c098"/></radialGradient>' +
      '<linearGradient id="ftHat" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#1f2937"/><stop offset="100%" stop-color="#0b0f16"/></linearGradient>' +
      '<linearGradient id="ftGold" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#fde68a"/><stop offset="100%" stop-color="#f59e0b"/></linearGradient>' +
    '</defs>' +
    shadow("#7f1d1d") + think("#fca5a5") +
    '<g class="avatar-float">' +
      '<path d="M50 190 Q48 136 80 128 Q100 122 120 128 Q152 136 150 190 Z" fill="url(#ftRobe)"/>' +
      '<path d="M100 128 Q88 158 86 190 L114 190 Q112 158 100 128 Z" fill="#fbbf24" opacity="0.9"/>' +
      '<path d="M84 150 Q100 142 116 150 Q108 158 100 158 Q92 158 84 150 Z" fill="url(#ftGold)" stroke="#b45309" stroke-width="1.5"/>' +
      '<g class="avatar-head">' +
        '<ellipse cx="100" cy="93" rx="34" ry="35" fill="url(#ftSkin)"/>' +
        '<ellipse cx="66" cy="96" rx="5.5" ry="8" fill="#f0b78a"/>' +
        '<ellipse cx="134" cy="96" rx="5.5" ry="8" fill="#f0b78a"/>' +
        '<path d="M62 72 Q58 54 100 54 Q142 54 138 72 L128 64 Q100 56 72 64 Z" fill="url(#ftHat)"/>' +
        '<rect x="60" y="58" width="80" height="14" rx="7" fill="url(#ftHat)"/>' +
        '<path d="M82 36 Q100 28 118 36 L116 58 L84 58 Z" fill="url(#ftHat)"/>' +
        '<circle cx="100" cy="46" r="10" fill="url(#ftGold)" stroke="#b45309" stroke-width="1.5"/>' +
        '<text x="100" y="50.5" font-size="11" text-anchor="middle" fill="#b45309" font-weight="bold">福</text>' +
        '<path d="M76 84 Q86 79 96 84" stroke="#3a2818" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
        '<path d="M104 84 Q114 79 124 84" stroke="#3a2818" stroke-width="2.4" fill="none" stroke-linecap="round"/>' +
        '<g class="avatar-eye">' +
          '<path d="M79 92 Q86 87 93 92" stroke="#2a1a10" stroke-width="3.2" fill="none" stroke-linecap="round"/>' +
          '<path d="M107 92 Q114 87 121 92" stroke="#2a1a10" stroke-width="3.2" fill="none" stroke-linecap="round"/>' +
        '</g>' +
        '<circle cx="73" cy="102" r="6.5" fill="#fb7185" opacity="0.5"/>' +
        '<circle cx="127" cy="102" r="6.5" fill="#fb7185" opacity="0.5"/>' +
        '<path d="M92 100 Q86 116 80 132 Q90 120 94 104 Z" fill="#e8e8e8"/>' +
        '<path d="M108 100 Q114 116 120 132 Q110 120 106 104 Z" fill="#e8e8e8"/>' +
        '<path class="avatar-mouth" d="M86 108 Q100 122 114 108 Q100 116 86 108 Z" fill="#9b2c2c"/>' +
        '<path d="M88 110 Q100 116 112 110 Q100 113 88 110 Z" fill="#f8d7da"/>' +
      "</g>" +
    "</g>"
  );

  var PRESETS = [
    { id: "advisor", name: "专业金融顾问", emoji: "🧑‍💼", svg: advisor },
    { id: "lady", name: "金融顾问(女)", emoji: "👩‍💼", svg: lady },
    { id: "mascot", name: "招财吉祥物", emoji: "🐣", svg: mascot },
    { id: "robot", name: "智能机器人", emoji: "🤖", svg: robot },
    { id: "westie", name: "西高地小狗", emoji: "🐶", svg: westie },
    { id: "panda", name: "招财熊猫", emoji: "🐼", svg: panda },
    { id: "fortune", name: "财神福星", emoji: "🧧", svg: fortune },
    { id: "cat", name: "布朗小猫", emoji: "🐱", svg: cat },
  ];

  /* -------- 自定义形象(参数化机器人) -------- */
  function darken(hex, f) {
    hex = hex.replace("#", "");
    if (hex.length === 3) hex = hex.split("").map(function (c) { return c + c; }).join("");
    var n = parseInt(hex, 16);
    var r = Math.round(((n >> 16) & 255) * f);
    var g = Math.round(((n >> 8) & 255) * f);
    var b = Math.round((n & 255) * f);
    return "rgb(" + r + "," + g + "," + b + ")";
  }

  var CUSTOM_OPTIONS = {
    primary: ["#3b82f6", "#06b6d4", "#8b5cf6", "#ec4899", "#22c55e", "#f59e0b", "#ef4444", "#64748b"],
    eye: ["#7dd3fc", "#a5f3fc", "#fde68a", "#fca5a5", "#86efac", "#c4b5fd", "#ffffff", "#1f2937"],
    head: [
      { id: "round", name: "圆形" },
      { id: "roundsquare", name: "圆角方" },
      { id: "square", name: "方形" },
    ],
    accessory: [
      { id: "glasses", name: "眼镜" },
      { id: "sunglasses", name: "墨镜" },
      { id: "skigoggles", name: "滑雪镜" },
      { id: "helmet", name: "头盔" },
      { id: "hat", name: "礼帽" },
      { id: "scarf", name: "围巾" },
      { id: "tie", name: "领带" },
      { id: "bowtie", name: "领结" },
      { id: "headphones", name: "耳机" },
    ],
  };

  var DEFAULT_CUSTOM = { primary: "#3b82f6", eye: "#7dd3fc", head: "roundsquare", accessories: ["glasses"], name: "我的顾问" };

  function headShape(shape, fillId, stroke) {
    if (shape === "round") {
      return '<circle cx="100" cy="84" r="44" fill="url(#' + fillId + ')" stroke="' + stroke + '" stroke-width="2"/>';
    }
    if (shape === "square") {
      return '<rect x="56" y="42" width="88" height="84" rx="10" fill="url(#' + fillId + ')" stroke="' + stroke + '" stroke-width="2"/>';
    }
    return '<rect x="56" y="44" width="88" height="80" rx="30" fill="url(#' + fillId + ')" stroke="' + stroke + '" stroke-width="2"/>';
  }

  function accessorySvg(kind, primary, secondary) {
    if (kind === "glasses") {
      return (
        '<g>' +
        '<rect x="74" y="78" width="20" height="16" rx="6" fill="none" stroke="#1f2937" stroke-width="2.5"/>' +
        '<rect x="106" y="78" width="20" height="16" rx="6" fill="none" stroke="#1f2937" stroke-width="2.5"/>' +
        '<line x1="94" y1="86" x2="106" y2="86" stroke="#1f2937" stroke-width="2.5"/>' +
        "</g>"
      );
    }
    if (kind === "sunglasses") {
      return (
        '<g>' +
        '<rect x="73" y="79" width="21" height="15" rx="6" fill="#1f2937"/>' +
        '<rect x="106" y="79" width="21" height="15" rx="6" fill="#1f2937"/>' +
        '<line x1="94" y1="85" x2="106" y2="85" stroke="#1f2937" stroke-width="3"/>' +
        '<line x1="73" y1="82" x2="60" y2="78" stroke="#1f2937" stroke-width="2.5"/>' +
        '<line x1="127" y1="82" x2="140" y2="78" stroke="#1f2937" stroke-width="2.5"/>' +
        '<line x1="77" y1="82" x2="84" y2="82" stroke="#94a3b8" stroke-width="2" stroke-linecap="round"/>' +
        "</g>"
      );
    }
    if (kind === "skigoggles") {
      return (
        '<g>' +
        '<path d="M52 86 H64 M136 86 H148" stroke="#1f2937" stroke-width="5" stroke-linecap="round"/>' +
        '<rect x="62" y="74" width="76" height="26" rx="13" fill="#0ea5e9" stroke="#1f2937" stroke-width="2.5"/>' +
        '<rect x="68" y="79" width="30" height="15" rx="7" fill="#bae6fd" opacity="0.7"/>' +
        '<rect x="104" y="79" width="26" height="15" rx="7" fill="#7dd3fc" opacity="0.5"/>' +
        "</g>"
      );
    }
    if (kind === "helmet") {
      return (
        '<g>' +
        '<path d="M56 86 Q56 38 100 38 Q144 38 144 86 Q100 72 56 86 Z" fill="' + primary + '"/>' +
        '<rect x="54" y="82" width="92" height="9" rx="4" fill="' + secondary + '"/>' +
        '<rect x="96" y="38" width="8" height="16" rx="3" fill="' + secondary + '"/>' +
        '<circle cx="100" cy="40" r="4" fill="#fef3c7"/>' +
        "</g>"
      );
    }
    if (kind === "hat") {
      return (
        '<g>' +
        '<rect x="60" y="40" width="80" height="7" rx="3" fill="#1f2937"/>' +
        '<path d="M74 40 H126 V26 Q100 16 74 26 Z" fill="#111827"/>' +
        '<rect x="74" y="34" width="52" height="6" fill="' + primary + '"/>' +
        "</g>"
      );
    }
    if (kind === "scarf") {
      return (
        '<g>' +
        '<path d="M70 116 Q100 134 130 116 L130 128 Q100 146 70 128 Z" fill="' + primary + '"/>' +
        '<path d="M112 124 L122 162 L134 158 L124 120 Z" fill="' + secondary + '"/>' +
        '<path d="M124 120 L134 158" stroke="' + primary + '" stroke-width="2" opacity="0.5"/>' +
        "</g>"
      );
    }
    if (kind === "tie") {
      return (
        '<g>' +
        '<path d="M100 116 l-7 6 l7 7 l7 -7 z" fill="' + primary + '"/>' +
        '<path d="M95 130 L91 162 L100 170 L109 162 L105 130 Z" fill="' + primary + '"/>' +
        "</g>"
      );
    }
    if (kind === "bowtie") {
      return (
        '<g>' +
        '<path d="M90 122 L78 115 V129 Z" fill="' + secondary + '"/>' +
        '<path d="M110 122 L122 115 V129 Z" fill="' + secondary + '"/>' +
        '<circle cx="100" cy="122" r="4" fill="' + primary + '"/>' +
        "</g>"
      );
    }
    if (kind === "headphones") {
      return (
        '<g>' +
        '<path d="M52 84 Q100 38 148 84" stroke="#374151" stroke-width="6" fill="none"/>' +
        '<rect x="46" y="80" width="13" height="26" rx="6" fill="#374151"/>' +
        '<rect x="141" y="80" width="13" height="26" rx="6" fill="#374151"/>' +
        '<rect x="49" y="86" width="7" height="14" rx="3" fill="' + primary + '"/>' +
        '<rect x="144" y="86" width="7" height="14" rx="3" fill="' + primary + '"/>' +
        "</g>"
      );
    }
    return "";
  }

  // 渲染配饰子集(按给定顺序),用于头部/颈部分层
  function renderAccessorySubset(list, subset, primary, secondary) {
    if (!list || !list.length) return "";
    var out = "";
    for (var i = 0; i < subset.length; i++) {
      if (list.indexOf(subset[i]) !== -1) out += accessorySvg(subset[i], primary, secondary);
    }
    return out;
  }
  var HEAD_WORN = ["headphones", "glasses", "sunglasses", "skigoggles", "helmet", "hat"];
  var NECK_WORN = ["scarf", "tie", "bowtie"];

  function normalizeAccessories(c) {
    // 向后兼容:旧版单选 accessory 字符串
    if (Array.isArray(c.accessories)) return c.accessories.slice();
    if (c.accessory && c.accessory !== "none") return [c.accessory];
    return [];
  }

  function buildCustom(cfg, idPrefix) {
    var c = {};
    for (var k in DEFAULT_CUSTOM) c[k] = DEFAULT_CUSTOM[k];
    if (cfg) for (var j in cfg) if (cfg[j] != null) c[j] = cfg[j];
    idPrefix = idPrefix || "cu";
    var headId = idPrefix + "Head";
    var bodyId = idPrefix + "Body";
    var primary = c.primary;
    var secondary = darken(primary, 0.62);
    var eye = c.eye;
    var acc = normalizeAccessories(c);

    var inner =
      '<defs>' +
        '<linearGradient id="' + headId + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="#ffffff"/><stop offset="100%" stop-color="#eef2ff"/></linearGradient>' +
        '<linearGradient id="' + bodyId + '" x1="0" y1="0" x2="0" y2="1"><stop offset="0%" stop-color="' + primary + '"/><stop offset="100%" stop-color="' + secondary + '"/></linearGradient>' +
      '</defs>' +
      shadow("#94a3b8") + think(eye) +
      '<g class="avatar-float">' +
        '<path d="M62 186 Q60 138 100 136 Q140 138 138 186 Z" fill="url(#' + bodyId + ')"/>' +
        '<circle class="avatar-twinkle" cx="100" cy="152" r="6" fill="' + eye + '"/>' +
        '<rect x="92" y="122" width="16" height="16" rx="5" fill="#cbd5e1"/>' +
        '<g class="avatar-head">' +
          headShape(c.head, headId, "#c7d2fe") +
          '<line x1="100" y1="' + (c.head === "round" ? "40" : "44") + '" x2="100" y2="30" stroke="#94a3b8" stroke-width="3"/>' +
          '<circle class="avatar-twinkle" cx="100" cy="26" r="5" fill="' + eye + '"/>' +
          '<rect x="68" y="70" width="64" height="36" rx="18" fill="' + secondary + '"/>' +
          '<g class="avatar-eye"><circle cx="86" cy="86" r="6" fill="' + eye + '"/><circle cx="114" cy="86" r="6" fill="' + eye + '"/></g>' +
          '<rect class="avatar-mouth" x="92" y="98" width="16" height="5" rx="2.5" fill="' + eye + '"/>' +
          renderAccessorySubset(acc, HEAD_WORN, primary, secondary) +
        "</g>" +
        renderAccessorySubset(acc, NECK_WORN, primary, secondary) +
      "</g>";
    return wrap(inner);
  }

  function getById(id) {
    for (var i = 0; i < PRESETS.length; i++) if (PRESETS[i].id === id) return PRESETS[i];
    return null;
  }

  global.AvatarLib = {
    presets: PRESETS,
    customOptions: CUSTOM_OPTIONS,
    defaultCustom: DEFAULT_CUSTOM,
    buildCustom: buildCustom,
    getById: getById,
  };
})(window);
