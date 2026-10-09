import { notFound } from "next/navigation";
import styles from "./CoursePresentationCard.module.css";
import { PrimaryLink } from "@/components/ui/PrimaryLink";
import f from "@/lib/formatters";



export default function CoursePresentationCard({course, enrollment}){
  const imgSrc = course.thumbnail ;
  let button;
  if(enrollment){
    const nextItem = "videoaula/?id=" + course.nextItem.id;
    button = (() => { return (
      <PrimaryLink className={styles.primaryButton}
        href={nextClass}>
        Pŕoxima aula
      </PrimaryLink>
    )})

  } else {
    const buyLink = "buy/?id=" + course.id;
    button = (() => { return (
      <PrimaryLink className={styles.primaryButton}
        href={buyLink}>Comprar</PrimaryLink>
    )});
  }

  const profName = course.teacher.treatment + " " + course.teacher.name;
  return (
    <div className={styles.card}>
      <img className={styles.cover} src={course.thumbnail}/>
      <div>
        <p className="tag-area"> {course.tags} </p>
        <div>
          <h1>{course.title}</h1>
          <p>{course.summary}</p>
          <p>{profName}</p>
          <div>
            <p>{f.Stars(course.rating)}</p>
            <p>{course.lessonCount + " aulas"}</p>
            <p></p>
            <p>{course.studentCount + " alunos"}</p>
          </div>
          {button()}
        </div>
      </div>
    </div>
  );

}
