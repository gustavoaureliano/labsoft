import Link from "next/link";
import f from "@/lib/formatters";

function ItemLine({displayIdx, programStruct}){
  const itemLink = "/videoaula/?id=" + programStruct.id;
  let displayTime = "...";
  if(programStruct.length){
    displayTime = f.Minutes(programStruct.length);
  }

  return (
    <Link href={itemLink}>
      <div className="card-item">
      <p>{displayIdx}</p>
      <p>{programStruct.name}</p>
      <p>{displayTime}</p>
      </div>
    </Link>
  );
}

export default function CourseProgramCard({programs}){
  if(programs){
    return(
      <div className="card">
        <h1>Conteúdo Programático</h1>
        <div className="item-list">
          {programs.map((program, idx) => (
              <ItemLine 
                key={program.id || idx}
                displayIdx={idx+1}
                programStruct={program}
              />
          ))}
        </div>
      </div>
    );
  } else {
    return(
      <div className="card">
        <h1>Conteúdo Programático</h1>
        <div className="item-list">
          <p> Nenhum conteúdo encontrado...</p>
        </div>
      </div>
    );

  }
}
