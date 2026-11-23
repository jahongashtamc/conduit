# Anime.js v4 — Timer (mahalliy nusxa)

Manba: https://animejs.com/documentation/timer (2026-11-23 tekshirildi).
Paket: `animejs@4.0.0` — `vendor/libraries/animejs/` ichida oflayn saqlangan. CDN ishlatilmaydi.

## Timer nima?

Timer — `setTimeout` / `setInterval` o'rniga ishlatiladigan, animatsiyalar va callback'larni bitta vaqt o'qida sinxronlashtiradigan obyekt.

```js
import { createTimer } from '/library/animejs/dist/anime.esm.js';

const timer = createTimer({
  duration: 1000,
  loop: true,
  frameRate: 30,
  onUpdate: (self) => {
    document.querySelector('.value').textContent = Math.round(self.progress * 100) + '%';
  },
  onLoop: (self) => console.log('loop', self.currentIteration),
});
```

## Parametrlar

- Ijro: `delay`, `duration`, `loop`, `loopDelay`, `alternate`, `reversed`, `autoplay`
- Vaqt: `frameRate`, `playbackRate`
- Callback: `onBegin`, `onComplete`, `onUpdate`, `onLoop`, `onPause`, `then()`

## Metodlar

`play`, `reverse`, `pause`, `restart`, `alternate`, `resume`, `complete`, `reset`, `cancel`, `revert`, `seek`, `stretch`.

## Boshqa bo'limlar

Animation, Timeline, Animatable, Draggable, Layout, Scope, Events, SVG, Text, Utilities, Easings, WAAPI, Engine, Adapters.

Mahalliy demo: `/library/animejs/demos/timer.html`.
