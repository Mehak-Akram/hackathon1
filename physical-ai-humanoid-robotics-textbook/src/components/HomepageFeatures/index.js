import clsx from 'clsx';
import Heading from '@theme/Heading';
import styles from './styles.module.css';

const FeatureList = [
  {
    title: 'Complete Learning Path',
    img: require('@site/static/img/img3.png').default,
    description: (
      <>
        A comprehensive journey from ROS 2 fundamentals to advanced humanoid robotics,
        covering simulation, perception, navigation, and vision-language-action systems.
      </>
    ),
  },
  {
    title: 'AI-Native Textbook',
    img: require('@site/static/img/img1.png').default,
    description: (
      <>
        Features RAG-compatible content with multilevel explanations, Urdu translations,
        and Claude subagent hooks for personalized learning experiences.
      </>
    ),
  },
  {
    title: 'Hands-On Approach',
    img: require('@site/static/img/img2.png').default,
    description: (
      <>
        Practical exercises, real-world examples, and capstone projects that bridge
        the gap between simulation and real hardware implementation.
      </>
    ),
  },
];

function Feature({img, title, description}) {
  return (
    <div className={clsx('col col--4')}>
      <div className="text--center">
        <img src={img} className={styles.featureSvg} alt={title} />
      </div>
      <div className="text--center padding-horiz--md">
        <Heading as="h3">{title}</Heading>
        <p>{description}</p>
      </div>
    </div>
  );
}

export default function HomepageFeatures() {
  return (
    <section className={styles.features}>
      <div className="container">
        <div className="row">
          {FeatureList.map((props, idx) => (
            <Feature key={idx} {...props} />
          ))}
        </div>
      </div>
    </section>
  );
}
