'use strict';
// Validated artwork routing. Kept separate so artwork can be upgraded without touching game logic.
bestStagePath = function(stage){
  const n=Math.max(0,Math.min(5,Number(stage)||0));
  return `assets/repair-art-${n}.webp?v=20260906d`;
};
