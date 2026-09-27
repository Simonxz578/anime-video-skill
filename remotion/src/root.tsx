import React from 'react';
import {Composition} from 'remotion';
import {Episode} from './episode';

export const Root: React.FC = () => <Composition
  id="KnowledgeEpisode"
  component={Episode}
  durationInFrames={1800}
  fps={30}
  width={1080}
  height={1920}
  defaultProps={{title: '为什么夜空是黑的？', subtitle: '光抵达这里的历史'}}
/>;
