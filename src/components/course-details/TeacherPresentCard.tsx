export default function TeacherPresentCard({teacher, contact}){
  const title = "Professor";
  const teacherPresent ="Prof. Fulano da Silva" ;
  const secondText =  "";
  return(
    <div>
    <h1>{title}</h1>
    <div>
      <h2>{teacherPresent}</h2>
      <p>{secondText}</p>
      <p>{teacher.about}</p>
      </div>
    </div>
  )
};
