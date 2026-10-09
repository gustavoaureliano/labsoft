import Link from "next/link";
import { AppShell } from "@/components/layout/AppShell";
import { getCoursePresentation } from "@/lib/adapters/course";
import styles from "./page.module.css";
import {EnrollmentStatus} from "@/data/course-details";

import CoursePresentationCard from "@/components/course-details/CoursePresentationCard";
import CourseProgramEnrolledCard from "@/components/course-details/CourseProgramEnrolledCard";
import CourseProgramCard from "@/components/course-details/CourseProgramCard";
import TeacherPresentCard from "@/components/course-details/TeacherPresentCard";
import CourseAboutCard from "@/components/course-details/CourseAboutCard";
import CoursePromoCard from "@/components/course-details/CoursePromoCard";


export default async function CourseDetails(
  { searchParams } : { searchParams: Promise<{id?: string}>;}
){
  const {id: courseId} = await searchParams;
  const userId = "u1"; //await getCtx()["user_id"];
  
  const courseData = getCoursePresentation(courseId, userId);
  if(!courseData) {
    return (
      <AppShell activePage="courses">
        <div>
          <h1>Erro! Curso Não Encontrado</h1>
          <p>Id do Curso: {courseId}</p>
        </div>
      </AppShell>
    )
  };

  if(courseData.enrollment === EnrollmentStatus.NOT_ENROLLED){
    return (
      <AppShell activePage="courses">
        <CoursePresentationCard course={courseData} enrollment={false}/>
        <CourseAboutCard course ={courseData}/>
        <CourseProgramCard programs={courseData.program}/>
        <TeacherPresentCard teacher={courseData.teacher} contact={false}/>
        <CoursePromoCard items={courseData.includes}/>
      </AppShell>
    )
  } else {
    return (
      <AppShell activePage="courses">
        <CoursePresentationCard course={courseData }enrollment={true}/>
        <CourseAboutCard course={courseData}/>
        <CourseProgramEnrolledCard course={courseData} enrollment={true}/>
        <TeacherPresentCard teacher={courseData.teacher} contact={true}/>
        {/* <CourseUserDetailsCard> */}
        <p> Teste Enrolled </p>
      </AppShell>
    )
  };
};
