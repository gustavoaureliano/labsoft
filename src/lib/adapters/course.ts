//import {mockCtx} from "@/data/courses-details";
//import {mockOrm} from "@/data/courses-details";
import  { mockCourseNotEnrolled } from "@/data/course-details";
import  { mockCourseEnrolled } from "@/data/course-details";


export function getCoursePresentation(courseId, userId){
  if(courseId === "fisica-quantica"){
    if(userId === "u1"){
      return mockCourseEnrolled;
    } else {
      return mockCourseNotEnrolled;
    };
  } else {
    return null;
  };
};

