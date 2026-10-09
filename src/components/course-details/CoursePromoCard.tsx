export default function CoursePromoCard({items}){

  return(
    <div>
      <h1>Você terá acesso:</h1>
      {items.map((i)=>{ return (
        <p>{"✓ " + i}</p>
      )})}
    </div>
  )
};
