import React from 'react';
import {AbsoluteFill, interpolate, useCurrentFrame} from 'remotion';

type Props = {title: string; subtitle: string};

// Composition contract only. The Python release gate does not invoke this until
// verified art, timed captions and mixed audio are supplied.
export const Episode: React.FC<Props> = ({title, subtitle}) => {
  const frame = useCurrentFrame();
  const drift = interpolate(frame, [0, 1800], [0, -70]);
  return <AbsoluteFill style={{background: 'linear-gradient(165deg, #071734, #173f7a 65%, #e9f4ff)', color: '#f7fbff', fontFamily: 'sans-serif', overflow: 'hidden'}}>
    <div style={{position: 'absolute', top: 260, left: 100, right: 100, transform: `translateY(${drift}px)`, fontSize: 86, lineHeight: 1.2, fontWeight: 600}}>{title}</div>
    <div style={{position: 'absolute', top: 1250, left: 100, right: 100, fontSize: 48, lineHeight: 1.4}}>{subtitle}</div>
  </AbsoluteFill>;
};
